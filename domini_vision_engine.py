import aiohttp
from google.genai import errors as genai_errors
from google.genai import types

import asyncio
import base64
import json
import os

from genai_exception import GeminiExceptionFactory
from genai_exception import GeminiResponseError
from genai_module_v2 import DEFAULT_MODEL
from genai_module_v2 import DotoriGemini
from genai_module_v2 import GEMINI_TIMEOUT_SECONDS


CLOUD_VISION_API_KEY_ENV_NAME = "CLOUD_VISION_API_KEY"
CLOUD_VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"
CLOUD_VISION_MAX_RESULTS = 20
VISION_PERSONA = "DotoriBot"
VISION_ANSWER_PROMPT = (
    "이미지와 이에 대한 Cloud Vision Web Detection 결과, 그리고 사용자의 원본 질문을 "
    "제공할 테니 이에 대한 적절한 답변을 생성하라"
)


class DominiVisionError(Exception):
    """이미지 검색 처리 예외."""


class DominiVisionEngine:
    """Cloud Vision 검색 결과와 Gemini 답변 생성 통합 엔진."""

    def __init__(
        self,
        cloud_vision_api_key: str | None = None,
        gemini_service: DotoriGemini | None = None,
    ):
        self.cloud_vision_api_key = (
            cloud_vision_api_key
            or os.getenv(CLOUD_VISION_API_KEY_ENV_NAME)
        )
        self.gemini_service = gemini_service or DotoriGemini()

    def build_vision_request(self, images: list[tuple[bytes, str]]) -> dict:
        """Cloud Vision Web Detection 일괄 요청 생성."""
        return {
            "requests": [
                {
                    "image": {
                        "content": base64.b64encode(image_data).decode("ascii"),
                    },
                    "features": [
                        {
                            "type": "WEB_DETECTION",
                            "maxResults": CLOUD_VISION_MAX_RESULTS,
                        }
                    ],
                }
                for image_data, _ in images
            ]
        }

    async def detect_web(
        self,
        images: list[tuple[bytes, str]],
    ) -> list[dict]:
        """Cloud Vision Web Detection 실행."""
        if not self.cloud_vision_api_key:
            raise DominiVisionError("Cloud Vision API 키 설정 없음")

        request_data = self.build_vision_request(images)

        try:
            timeout = aiohttp.ClientTimeout(total=GEMINI_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    CLOUD_VISION_API_URL,
                    params={"key": self.cloud_vision_api_key},
                    json=request_data,
                ) as response:
                    response_data = await response.json(content_type=None)

                    if response.status >= 400:
                        error_data = response_data.get("error", {})
                        error_code = error_data.get("status", response.status)
                        error_message = error_data.get(
                            "message",
                            "Cloud Vision API 요청 실패",
                        )
                        print(f"[ERROR][{error_code}] {error_message}")
                        raise DominiVisionError(error_message)
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            print(f"[ERROR][CLOUD_VISION_REQUEST] {error}")
            raise DominiVisionError("Cloud Vision API 연결 실패") from error

        responses = response_data.get("responses", [])
        detection_results = []

        for response_index, detection_response in enumerate(responses, start=1):
            error_data = detection_response.get("error")
            if error_data:
                error_code = error_data.get("code", "CLOUD_VISION_RESPONSE")
                error_message = error_data.get("message", "Web Detection 실패")
                print(f"[ERROR][{error_code}] {error_message}")
                raise DominiVisionError(
                    f"{response_index}번째 이미지 Web Detection 실패"
                )

            detection_results.append(
                detection_response.get("webDetection", {})
            )

        if len(detection_results) != len(images):
            raise DominiVisionError("Cloud Vision 응답 이미지 수 불일치")

        return detection_results

    def build_gemini_contents(
        self,
        user_prompt: str,
        images: list[tuple[bytes, str]],
        detection_results: list[dict],
    ) -> tuple[str, list[types.Content]]:
        """DotoriBot 페르소나 기반 멀티모달 Gemini 콘텐츠 생성."""
        instruction, contents = self.gemini_service.build_contents(
            "",
            VISION_PERSONA,
        )
        contents.pop()

        request_parts = [
            types.Part(
                text=(
                    f"{VISION_ANSWER_PROMPT}\n\n"
                    f"사용자의 원본 질문:\n{user_prompt}"
                )
            )
        ]

        for image_index, ((image_data, mime_type), detection_result) in enumerate(
            zip(images, detection_results),
            start=1,
        ):
            request_parts.append(types.Part(text=f"원본 이미지 {image_index}:"))
            request_parts.append(
                types.Part.from_bytes(
                    data=image_data,
                    mime_type=mime_type,
                )
            )
            request_parts.append(
                types.Part(
                    text=(
                        f"이미지 {image_index}의 Cloud Vision Web Detection 결과:\n"
                        f"{json.dumps(detection_result, ensure_ascii=False)}"
                    )
                )
            )

        contents.append(types.Content(role="user", parts=request_parts))
        return instruction, contents

    async def generate_answer(
        self,
        user_prompt: str,
        images: list[tuple[bytes, str]],
        detection_results: list[dict],
    ) -> str:
        """원본 이미지와 검색 결과 기반 Gemini 답변 생성."""
        instruction, contents = self.build_gemini_contents(
            user_prompt,
            images,
            detection_results,
        )

        try:
            response = await asyncio.wait_for(
                self.gemini_service.client.aio.models.generate_content(
                    model=DEFAULT_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=instruction,
                    ),
                ),
                timeout=GEMINI_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as error:
            GeminiExceptionFactory.raise_timeout_exception(error)
        except genai_errors.APIError as error:
            GeminiExceptionFactory.raise_exception(error)
        except Exception as error:
            print(f"[ERROR][GEMINI_VISION_ANSWER] {error}")
            raise

        if not response.text:
            raise GeminiResponseError("Gemini 이미지 검색 답변 데이터 없음")

        return response.text

    async def search_images(
        self,
        user_prompt: str,
        images: list[tuple[bytes, str]],
    ) -> str:
        """Web Detection부터 DotoriBot 답변까지 순차 실행."""
        detection_results = await self.detect_web(images)
        return await self.generate_answer(
            user_prompt,
            images,
            detection_results,
        )
