"""
List available Gemini models that support text generation.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ GEMINI_API_KEY not found in .env file!")
    exit(1)

genai.configure(api_key=api_key)

print("🔍 Available Gemini models for text generation:")
print("=" * 60)

try:
    models = genai.list_models()
    text_models = [m for m in models if 'generateContent' in m.supported_generation_methods]
    
    for model in text_models:
        # Extract just the model name after "models/"
        model_name = model.name.replace('models/', '')
        print(f"✅ {model_name}")
    
    print("=" * 60)
    print(f"\nTotal: {len(text_models)} models available")
    
    if text_models:
        print("\n💡 Recommended models to try:")
        recommended = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        for rec in recommended:
            if any(rec in m.name for m in text_models):
                print(f"   • {rec}")
    
except Exception as e:
    print(f"❌ Error listing models: {e}")
    print("\n💡 Try these common model names:")
    print("   • gemini-1.5-flash")
    print("   • gemini-1.5-pro")
    print("   • gemini-pro")
