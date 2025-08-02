import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')
print('API key exists:', bool(api_key))

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=[types.Content(role='user', parts=[types.Part(text='What is 2+2?')])],
    )
    print('Response received:', response)
    print('Response text:', getattr(response, 'text', 'No text attribute'))
except Exception as e:
    print('Error:', e)
