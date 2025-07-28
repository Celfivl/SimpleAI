import os, sys, argparse
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

from google import genai

client = genai.Client(api_key=api_key)

from google.genai import types


parser = argparse.ArgumentParser()
parser.add_argument("prompt", help="The user's prompt") 
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()
user_prompt = args.prompt
is_verbose = args.verbose 

def main():
    messages = [
    types.Content(role="user", parts=[types.Part(text=user_prompt)]),
]
    if len(sys.argv) < 2:
        print("Error: Please provide a prompt")
        sys.exit(1)

    if args.verbose:
        print(f"User prompt: {user_prompt}")

    print("Hello from simpleai!")
    response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents=messages
    )
     # Print the AI's response
    print(response.text)
    
    if args.verbose:
        # Print the token usage information
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

if __name__ == "__main__":
    main()
