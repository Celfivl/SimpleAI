import os, sys, argparse, json
from dotenv import load_dotenv
from functions.get_files_info import schema_get_files_info, schema_get_file_content, schema_run_python_file, schema_write_file
from functions.get_files_info import get_files_info, get_file_content, write_file
from functions.run_python import run_python_file

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

from google import genai

client = genai.Client(api_key=api_key)

from google.genai import types

system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,  
        schema_run_python_file,  
        schema_write_file,       
    ]
)

parser = argparse.ArgumentParser()
parser.add_argument("prompt", help="The user's prompt") 
parser.add_argument("--verbose", action="store_true")
args = parser.parse_args()
user_prompt = args.prompt
is_verbose = args.verbose 

# Define the hardcoded working directory
WORKING_DIRECTORY = "./calculator"

# --- Dictionary mapping function names (strings) to actual function objects ---
# This allows dynamic calling using function_map[function_name](**kwargs)
function_map = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}

def call_function(function_call_part, verbose=False):
    """
    Handles the abstract task of logging a function call requested by the LLM.

    """
    function_name = function_call_part.name
    function_args = dict(function_call_part.args) # Convert to mutable dictionary

    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    if function_name not in function_map:
        # If the function name is not recognized, return an error message
        return types.Content(
    role="tool",
    parts=[
        types.Part.from_function_response(
            name=function_name,
            response={"error": f"Unknown function: {function_name}"},
        )
    ],
)

    # Manually add the working_directory parameter for security
    function_args['working_directory'] = WORKING_DIRECTORY

    try:
        # Dynamically call the function with the unpacked arguments
        # The '**' operator unpacks the dictionary into keyword arguments
        result = function_map[function_name](**function_args)
         # Return types.Content with a from_function_response describing the result
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"result": result},
                )
            ],
        )
    except Exception as e:
        # Catch any exceptions during the actual function execution
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Error executing function '{function_name}': {e}"},
                )
            ],
        )


def main():
    messages = [
    types.Content(role="user", parts=[types.Part(text=user_prompt)]),
]
    if len(sys.argv) < 2:
        print("Error: Please provide a prompt")
        sys.exit(1)

    if args.verbose:
        print(f"User prompt: {user_prompt}")

    response = client.models.generate_content(
    model='gemini-2.0-flash-001', contents=messages,
    config=types.GenerateContentConfig(tools=[available_functions], system_instruction=system_prompt),
    )
   
   # --- Check for function calls ---
    if response.function_calls:
        for function_call_part in response.function_calls:
            # Call the function using call_function and capture the result
            # The call_function should now return types.Content as per our last successful interaction
            function_call_result = call_function(function_call_part, verbose=is_verbose)

            # Ensure the result is a types.Content object and has the expected structure
            if not (isinstance(function_call_result, types.Content) and
                    function_call_result.parts and
                    function_call_result.parts[0].function_response and
                    hasattr(function_call_result.parts[0].function_response, 'response')):
                raise ValueError("Fatal Error: call_function did not return a valid "
                                 "types.Content with .parts[0].function_response.response")

            # Access the actual response from the tool
            actual_response_data = function_call_result.parts[0].function_response.response

            if is_verbose:
                    # Print the result of the function call as requested
                print(f"-> {actual_response_data}")
    
    elif response.text:
            # Print the AI's text response if no function call was made
        print(response.text)
    else:
            # Handle cases where there might be no text or function call (e.g., safety block)
        print("No response text or function call was received.")
    
if args.verbose:
         # Print the token usage information
    print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
    print(f"Response tokens: {response.usage_metadata.candidates_token_count}")

if __name__ == "__main__":
    main()
