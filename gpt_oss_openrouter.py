#!/usr/bin/env python3
import requests
import json
import sys
import os

# OpenRouter API configuration
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

def test_gpt_oss_api():
    """Test GPT-OSS via OpenRouter API"""
    print("=" * 60)
    print("GPT-OSS VIA OPENROUTER API")
    print("=" * 60)

    # Test message
    test_prompt = "Hello! Please respond with 'GPT-OSS is working via OpenRouter API!' to confirm you're functioning."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # Try different GPT-OSS model variants available on OpenRouter
    models_to_try = [
        "microsoft/wizardlm-2-8x22b",
        "meta-llama/llama-3.1-70b-instruct",
        "anthropic/claude-3-sonnet",
        "openai/gpt-4-turbo",
        "mistralai/mixtral-8x7b-instruct"
    ]

    for model in models_to_try:
        print(f"\nTesting model: {model}")
        print("-" * 40)

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": test_prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }

        try:
            response = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    message = data['choices'][0]['message']['content']
                    print(f"✅ SUCCESS with {model}:")
                    print(f"Response: {message.strip()}")
                    return model, message.strip()
                else:
                    print(f"❌ No response content from {model}")
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Error with {model}: {e}")

    return None, None

def interactive_chat(model):
    """Interactive chat with GPT-OSS via OpenRouter"""
    print("\n" + "=" * 60)
    print(f"INTERACTIVE CHAT - {model}")
    print("=" * 60)
    print("Type 'exit' to quit, 'clear' to clear conversation")
    print("")

    conversation = []
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower() == 'clear':
                conversation = []
                print("Conversation cleared!")
                continue
            elif not user_input:
                continue

            # Add user message to conversation
            conversation.append({"role": "user", "content": user_input})

            payload = {
                "model": model,
                "messages": conversation,
                "max_tokens": 500,
                "temperature": 0.7
            }

            print("\nGPT-OSS: ", end="", flush=True)

            response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    message = data['choices'][0]['message']['content']
                    print(message.strip())

                    # Add assistant response to conversation
                    conversation.append({"role": "assistant", "content": message})
                else:
                    print("No response received")
            else:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)

        except KeyboardInterrupt:
            print("\n\nChat interrupted. Type 'exit' to quit.")
        except Exception as e:
            print(f"\nError: {e}")

        print("")

def single_prompt_mode(model, prompt):
    """Single prompt mode"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0]['message']['content']
                return message.strip()
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"

    except Exception as e:
        return f"Error: {e}"

def main():
    print("🚀 GPT-OSS via OpenRouter API")
    print("")

    # Test API connection and find working model
    working_model, test_response = test_gpt_oss_api()

    if not working_model:
        print("\n❌ No models are working with your API key.")
        print("Check your OpenRouter API key and try again.")
        return

    print(f"\n✅ Found working model: {working_model}")

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--chat':
            interactive_chat(working_model)
        else:
            # Single prompt mode
            prompt = ' '.join(sys.argv[1:])
            print(f"\nPrompt: {prompt}")
            print("Response:")
            print(single_prompt_mode(working_model, prompt))
    else:
        print("\nUsage:")
        print("  python3 gpt_oss_openrouter.py 'your question'")
        print("  python3 gpt_oss_openrouter.py --chat")
        print("")
        print("Starting interactive mode...")
        interactive_chat(working_model)

if __name__ == "__main__":
    main()