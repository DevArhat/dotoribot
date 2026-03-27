import os
import json
import dotenv
from google import genai
from google.genai import types
from logic import BASE_DIR

# .env 파일 로드
dotenv.load_dotenv()

# system_prompts.json 경로 설정
PROMPT_PATH = os.path.join(BASE_DIR, "system_prompts.json")

def load_system_prompts():
    """system_prompts.json 파일을 읽어서 반환합니다."""
    try:
        with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# 모듈 로드시 프롬프트 데이터 초기 로드
_SYSTEM_PROMPTS = load_system_prompts()

def reload_system_prompts():
    """프롬프트 데이터를 다시 로드합니다."""
    global _SYSTEM_PROMPTS
    _SYSTEM_PROMPTS = load_system_prompts()

def call_genai(user_input: str, persona: str = 'DotoriBot'):
    """
    Gemini API를 호출하여 응답을 생성합니다.
    
    :param user_input: 사용자 입력 문자열
    :param persona: 사용할 페르소나 이름 (system_prompts.json의 키)
    :return: 모델의 응답 텍스트
    """
    client = genai.Client(api_key=os.getenv('GEMINI_KEY'))

    # 해당 페르소나 데이터 가져오기 (없으면 기본 DotoriBot 사용)
    persona_data = _SYSTEM_PROMPTS.get(persona)
    if not persona_data:
        persona_data = _SYSTEM_PROMPTS.get('DotoriBot', {})
    
    instruction = persona_data.get('instruction', '')
    few_shot_history = persona_data.get('few_shot_history', [])

    # Gemini SDK 형식에 맞게 contents 구성
    contents = []
    
    # 1. Few-shot history 추가
    for item in few_shot_history:
        contents.append(types.Content(
            role=item['role'],
            parts=[types.Part(text=p['text']) for p in item['parts']]
        ))
    
    # 2. 현재 사용자 입력 추가
    contents.append(types.Content(
        role='user',
        parts=[types.Part(text=user_input)]
    ))

    # API 호출
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=instruction
        )
    )
    
    return response.text
