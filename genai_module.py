import os
import json
import dotenv

from google import genai
from google.genai import types

from logic import BASE_DIR


dotenv.load_dotenv()

PROMPT_PATH = os.path.join(BASE_DIR, "system_prompts.json")
try:
    with open(PROMPT_PATH, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
        SYSTEM_PROMPT = prompts.get('DotoriBot', '')
except FileNotFoundError:
    SYSTEM_PROMPT = ""

def call_genai(user_input: str):
    client = genai.Client(api_key=os.getenv('GEMINI_KEY'))

    response = client.models.generate_content(
        model = 'gemini-3.1-flash-lite-preview',
        contents = user_input,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )
    return response.text
