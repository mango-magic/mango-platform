#!/usr/bin/env python3
"""
Test script to list available Gemini models
"""

import os
import google.generativeai as genai

# Configure with API key from environment
api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyDGH8vz2YrPw5-gYZ0lYXgKvVf8z3jFt9E')
genai.configure(api_key=api_key)

print("🔍 Listing available Gemini models...\n")

try:
    # List all available models
    models = genai.list_models()
    
    print("✅ Available models that support generateContent:\n")
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
            print(f"    Display name: {model.display_name}")
            print(f"    Description: {model.description[:80]}...")
            print()
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying basic model test...")
    
    # Try a few common model names
    test_models = [
        'gemini-pro',
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-1.0-pro',
        'models/gemini-pro',
    ]
    
    for model_name in test_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Say 'test'")
            print(f"✅ {model_name} WORKS!")
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")

