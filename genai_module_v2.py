import dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types


import asyncio
import base64
import json
import os


from genai_exception import GeminiConfigurationError
from genai_exception import GeminiExceptionFactory
from genai_exception import GeminiResponseError
from logic import BASE_DIR


# .env 파일 로드
dotenv.load_dotenv(override=True)

# Gemini 및 시스템 프롬프트 기본 설정
API_KEY_ENV_NAME = "GEMINI_API_KEY"
DEFAULT_IMAGE_ASPECT_RATIO = "16:9"
DEFAULT_IMAGE_MIME_TYPE = "image/jpeg"
DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image"
DEFAULT_IMAGE_SIZE = "2K"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_PERSONA = "DotoriBot"
GEMINI_TIMEOUT_MILLISECONDS = 150000
GEMINI_TIMEOUT_SECONDS = 150
PROMPT_PATH = os.path.join(BASE_DIR, "system_prompts.json")


class DotoriGemini:
    """Gemini 클라이언트와 페르소나 프롬프트 관리 클래스."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        prompt_path: str = PROMPT_PATH,
    ):
        self.model = model
        self.prompt_path = prompt_path
        self.client = self.create_client(api_key)
        self.system_prompts = self.load_system_prompts()

    def create_client(self, api_key: str | None = None):
        """명시된 키 또는 환경변수 기반 Gemini 클라이언트 생성."""
        environment_api_key = os.getenv(API_KEY_ENV_NAME)
        resolved_api_key = api_key or environment_api_key
        http_options = types.HttpOptions(
            timeout=GEMINI_TIMEOUT_MILLISECONDS,
        )

        try:
            if resolved_api_key:
                return genai.Client(
                    api_key=resolved_api_key,
                    http_options=http_options,
                )

            # SDK의 기본 인증 환경변수 및 Vertex AI 설정 탐색 동작 사용
            return genai.Client(http_options=http_options)
        except Exception as error:
            print(f"[ERROR][GEMINI_CLIENT_INIT] Gemini 클라이언트 생성 실패: {error}")
            raise GeminiConfigurationError(
                "Gemini 클라이언트 생성 실패"
            ) from error

    def load_system_prompts(self) -> dict:
        """시스템 프롬프트 파일 로드."""
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as prompt_file:
                return json.load(prompt_file)
        except (OSError, json.JSONDecodeError) as error:
            print(f"[WARN] 시스템 프롬프트 로드 실패: {error}")
            return {}

    def reload_system_prompts(self) -> dict:
        """시스템 프롬프트 데이터 갱신."""
        self.system_prompts = self.load_system_prompts()
        return self.system_prompts

    def build_contents(self, user_input: str, persona: str) -> tuple[str, list[types.Content]]:
        """페르소나 지시문과 Gemini 요청 콘텐츠 구성."""
        persona_data = self.system_prompts.get(persona)
        if not persona_data:
            persona_data = self.system_prompts.get(DEFAULT_PERSONA, {})

        instruction = persona_data.get("instruction", "")
        few_shot_history = persona_data.get("few_shot_history", [])
        contents = []

        for item in few_shot_history:
            contents.append(
                types.Content(
                    role=item["role"],
                    parts=[types.Part(text=part["text"]) for part in item["parts"]],
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_input)]
            )
        )
        return instruction, contents


    async def call_genai(
        self,
        user_input: str,
        persona: str | None = DEFAULT_PERSONA,
    ) -> str:
        if persona is not None:
            instruction, contents = self.build_contents(user_input, persona)
        else:
            instruction = None
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_input)],
                )
            ]

        try:
            async with asyncio.timeout(GEMINI_TIMEOUT_SECONDS):
                response = await self.client.aio.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=instruction,
                        tools=[types.Tool(google_search=types.GoogleSearch())],
                    ),
                )
        except TimeoutError as error:
            GeminiExceptionFactory.raise_timeout_exception(error)
        except genai_errors.APIError as error:
            GeminiExceptionFactory.raise_exception(error)
        except Exception as error:
            print(f"[ERROR][GEMINI_GENERATE_CONTENT] Gemini 응답 생성 실패: {error}")
            raise

        return response.text

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_IMAGE_ASPECT_RATIO,
        image_size: str = DEFAULT_IMAGE_SIZE,
        mime_type: str = DEFAULT_IMAGE_MIME_TYPE,
    ) -> bytes:
        """Gemini Interactions API 기반 이미지 데이터 생성."""
        try:
            async with asyncio.timeout(GEMINI_TIMEOUT_SECONDS):
                interaction = await self.client.aio.interactions.create(
                    model=DEFAULT_IMAGE_MODEL,
                    input=prompt + "\n\n" + "Use the Google Search tool for information that requires up-to-date verification or when encountering unfamiliar proper nouns, terms, or entities.",
                    tools=[{"type": "google_search"}],
                    response_format={
                        "type": "image",
                        "mime_type": mime_type,
                        "aspect_ratio": aspect_ratio,
                        "image_size": image_size,
                    },
                )

                if not interaction.output_image or not interaction.output_image.data:
                    raise GeminiResponseError("Gemini 이미지 응답 데이터 없음")

                return base64.b64decode(interaction.output_image.data)
        except TimeoutError as error:
            GeminiExceptionFactory.raise_timeout_exception(error)
        except genai_errors.APIError as error:
            GeminiExceptionFactory.raise_exception(error)
        except GeminiResponseError as error:
            print(f"[ERROR][GEMINI_IMAGE_RESPONSE] {error}")
            raise
        except Exception as error:
            print(f"[ERROR][GEMINI_GENERATE_IMAGE] Gemini 이미지 생성 실패: {error}")
            raise
    
            


_default_gemini = None


def get_default_gemini() -> DotoriGemini:
    """기본 DotoriGemini 인스턴스 지연 생성."""
    global _default_gemini

    if _default_gemini is None:
        _default_gemini = DotoriGemini()

    return _default_gemini


def reload_system_prompts() -> dict:
    """기본 인스턴스의 시스템 프롬프트 데이터 갱신."""
    return get_default_gemini().reload_system_prompts()


async def call_genai(user_input: str, persona: str = DEFAULT_PERSONA) -> str:
    """기존 함수 호출 방식과 호환되는 Gemini API 응답 생성."""
    return await get_default_gemini().call_genai(user_input, persona)
