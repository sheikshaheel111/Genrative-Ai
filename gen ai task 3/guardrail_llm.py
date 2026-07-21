import urllib.request
import urllib.error
import json
import re
import sys

# Ollama default configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2" # Change this to the model you have installed in Ollama (e.g., 'mistral', 'phi3')

# Simple rule-based guardrail using regex
UNSAFE_PATTERNS = [
    r"ignore\s+(your\s+)?(guidelines|instructions|system prompt|rules)",
    r"override\s+(your\s+)?(instructions|guidelines|system prompt|rules)",
    r"reveal\s+(your\s+)?(system prompt|instructions|rules)",
    r"bypass\s+(your\s+)?(instructions|guidelines|system prompt|rules)",
    r"jailbreak",
    r"forget\s+(all\s+)?previous\s+(instructions|prompts)",
    r"do anything now",
    r"dan" # common jailbreak prompt name
]

def check_prompt_safety(prompt: str) -> bool:
    """
    Checks if the prompt contains unsafe instructions or prompt injection attempts.
    Returns True if safe, False otherwise.
    """
    prompt_lower = prompt.lower()
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, prompt_lower):
            return False
    return True

def query_ollama(prompt: str) -> str:
    """
    Sends the safe prompt to the local Ollama model.
    """
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        OLLAMA_URL, 
        data=data, 
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "")
    except urllib.error.URLError as e:
        return f"Error communicating with Ollama: {e}\n(Make sure Ollama is running and you have pulled the '{MODEL}' model.)"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("Welcome to the Guardrailed LLM Chat!")
    print("Type 'exit' or 'quit' to stop.\n")
    
    while True:
        try:
            user_prompt = input("User Prompt: ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
            
        if user_prompt.strip().lower() in ['exit', 'quit']:
            break
            
        if not user_prompt.strip():
            continue
            
        print("↓ Guardrail")
        is_safe = check_prompt_safety(user_prompt)
        
        if is_safe:
            print("Safe")
            print("↓ Sent to Ollama")
            print("Output: Response:")
            response = query_ollama(user_prompt)
            print(f'"{response.strip()}"\n')
        else:
            print("Potential Prompt Injection Detected")
            print("Reason:")
            print("Attempt to override system instructions.")
            print("Request not sent to the LLM.")
            print("Output:\n")
            print("Request Blocked. This prompt violates AI safety guidelines.\n")

if __name__ == "__main__":
    main()
