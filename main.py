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

        # --- Loop for repeated calls to generate_content ---
    for i in range(20):  # Limit to 20 iterations
        if args.verbose:
            print(f"\n--- Iteration {i+1} ---")

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=messages,
                config=types.GenerateContentConfig(tools=[available_functions], system_instruction=system_prompt),
            )

            # Add model's candidates to messages list (for tool use history)
            if response.candidates:
                for candidate in response.candidates:
                    messages.append(candidate.content)

            # Check for function calls and execute them
            if response.function_calls:
                for function_call_part in response.function_calls:
                    function_call_result = call_function(function_call_part, verbose=is_verbose)

                    # Validate the structure of the returned types.Content
                    if not (isinstance(function_call_result, types.Content) and
                            function_call_result.parts and
                            function_call_result.parts[0].function_response and
                            hasattr(function_call_result.parts[0].function_response, 'response')):
                        raise ValueError("Fatal Error: call_function did not return a valid "
                                         "types.Content with .parts[0].function_response.response")

                    actual_response_data = function_call_result.parts[0].function_response.response

                    if is_verbose:
                        print(f"-> {actual_response_data}")

                    messages.append(function_call_result) # Add the tool's response to messages

            elif response.text:
                # If a text response is received, it means the model is done or providing
                # a direct answer. Print and break the loop.
                print(response.text)
                break # Exit the loop as the conversation is likely complete
            else:
                # Handle cases where there might be no text or function call (e.g., safety block)
                print("No response text or function call was received. Ending conversation.")
                break # Break if nothing useful is returned

        except Exception as e:
            # Handle any exceptions during the generate_content call or processing
            print(f"Error during iteration {i+1}: {e}")
            break # Break the loop on error

    else: # This 'else' belongs to the for loop, executes if loop completes without a 'break'
        print("\nWarning: Maximum iterations reached without a final response.")


    if args.verbose:
        # Print the token usage information for the *last* response
        if 'response' in locals() and response.usage_metadata:
            print(f"\nPrompt tokens (last response): {response.usage_metadata.prompt_token_count}")
            print(f"Response tokens (last response): {response.usage_metadata.candidates_token_count}")
        else:
            print("\nToken usage information not available for the last response.")

if __name__ == "__main__":
    main()
