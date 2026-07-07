import os
import toml
from supabase import create_client
import google.generativeai as genai

secrets_path = os.path.join('.streamlit', 'secrets.toml')
with open(secrets_path, 'r') as f: secrets = toml.load(f)

print('Connecting to Supabase...')
url = secrets.get('url')
key = secrets.get('key')
supabase = create_client(url, key)

print('Connecting to Gemini...')
genai.configure(api_key=secrets.get('gemini_api_key'))
model = genai.GenerativeModel('gemini-1.5-flash')

print('Calling Gemini...')
try:
    response = model.generate_content('Di Hola Mundo')
    print('Gemini responded:', response.text)
except Exception as e:
    print('Error:', e)
