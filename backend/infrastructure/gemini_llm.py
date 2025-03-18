from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Now you can access the environment variable
google_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")


import google.generativeai as genai

genai.configure(api_key=google_credentials)  # Gemini uses API Key, not GCP key

models = genai.list_models()
# for model in models:
#     print(model.name)
def ask_gemini(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    response = model.generate_content(prompt)
    return response