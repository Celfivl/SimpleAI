import os, sys, argparse, json, tiktoken
from dotenv import load_dotenv
from functions.get_files_info import schema_get_files_info, schema_get_file_content, schema_run_python_file, schema_write_file
from functions.get_files_info import get_files_info, get_file_content, write_file
from functions.run_python import run_python_file

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories
- Read file contents
- Execute Python files with optional arguments
- Write or overwrite files

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

MAX_CONTEXT_TOKENS = 100000
ENCODING = tiktoken.encoding_for_model("gpt-4")

def count_tokens(messages):
    """
    Counts the approximate number of tokens in a list of Gemini API messages.
    """
    token_count = 0
    for message in messages:
        # Each message has overhead tokens beyond its content
        token_count += 4 # Message overhead (e.g., role, parts, etc.)
        for part in message.parts:
            if hasattr(part, 'text') and part.text:
                token_count += len(ENCODING.encode(part.text))
            elif hasattr(part, 'function_call') and part.function_call:
                # Add tokens for function name and arguments
                token_count += len(ENCODING.encode(part.function_call.name))
                for arg_name, arg_value in part.function_call.args.items():
                    token_count += len(ENCODING.encode(arg_name))
                    token_count += len(ENCODING.encode(str(arg_value)))
            elif hasattr(part, 'function_response') and part.function_response:
                # Add tokens for function name and response
                token_count += len(ENCODING.encode(part.function_response.name))
                for key, value in part.function_response.response.items():
                    token_count += len(ENCODING.encode(key))
                    token_count += len(ENCODING.encode(str(value)))
    return token_count

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)

WORKING_DIRECTORY = "./calculator"

function_map = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "run_python_file": run_python_file,
    "write_file": write_file,
}

def call_function(function_call_part, verbose=False):
    function_name = function_call_part.name
    function_args = dict(function_call_part.args)

    if verbose:
        print(f"Calling function: {function_name}({function_args})")
    else:
        print(f" - Calling function: {function_name}")

    if function_name not in function_map:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    function_args['working_directory'] = WORKING_DIRECTORY

    try:
        function_result = function_map[function_name](**function_args)
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"result": function_result},
                )
            ],
        )
    except Exception as e:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Error executing function '{function_name}': {e}"},
                )
            ],
        )


def run_ai_query(user_input, is_verbose_mode):
    # This messages list will be built up and potentially trimmed
    messages = [
        types.Content(role="user", parts=[types.Part(text=user_input)]),
    ]

    response_text_output = ""
    current_tokens = count_tokens(messages) # Get initial token count

    for i in range(20):
        if is_verbose_mode:
            print(f"\n--- Iteration {i+1} --- (Current Tokens: {current_tokens})")

        # --- Token Recycling: Trim messages if exceeding limit before calling API ---
        while current_tokens > MAX_CONTEXT_TOKENS:
            if len(messages) <= 1: # Always keep at least the initial user message
                if is_verbose_mode:
                    print("Warning: Cannot trim messages further, context window exceeded.")
                break
            
            removed_message = messages.pop(0) # Remove the oldest message
            current_tokens = count_tokens(messages) # Recalculate tokens after removal
            if is_verbose_mode:
                print(f"  - Trimmed oldest message. New token count: {current_tokens}")
        # --- End Token Recycling ---

        try:
            response = client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=messages, # Pass the potentially trimmed messages list
                config=types.GenerateContentConfig(tools=[available_functions], system_instruction=system_prompt),
            )

            # Add model's candidates to messages list (for tool use history)
            if response.candidates:
                for candidate in response.candidates:
                    messages.append(candidate.content)
                    current_tokens = count_tokens(messages) # Update token count
                    if is_verbose_mode:
                        print(f"  - Appended candidate. New token count: {current_tokens}")

            # Check for function calls and execute them
            if response.function_calls:
                for function_call_part in response.function_calls:
                    function_call_result = call_function(function_call_part, verbose=is_verbose_mode)

                    if not (isinstance(function_call_result, types.Content) and
                            function_call_result.parts and
                            function_call_result.parts.function_response and
                            hasattr(function_call_result.parts.function_response, 'response')):
                        response_text_output = f"Error: Invalid function call result format from LLM."
                        if is_verbose_mode: print(response_text_output)
                        return response_text_output

                    actual_response_data = function_call_result.parts.function_response.response

                    if is_verbose_mode:
                        print(f"-> {actual_response_data}")

                    messages.append(function_call_result)
                    current_tokens = count_tokens(messages) # Update token count
                    if is_verbose_mode:
                        print(f"  - Appended function result. New token count: {current_tokens}")


            elif response.text:
                response_text_output = response.text
                if is_verbose_mode: print(response_text_output)
                messages.append(types.Content(role="model", parts=[types.Part(text=response_text_output)]))
                current_tokens = count_tokens(messages) # Update token count one last time
                if is_verbose_mode:
                        print(f"  - Appended final text response. New token count: {current_tokens}")
                break
            else:
                response_text_output = "No response text or function call was received. Ending conversation."
                if is_verbose_mode: print(response_text_output)
                break

        except Exception as e:
            response_text_output = f"Error during AI interaction: {e}"
            if is_verbose_mode: print(response_text_output)
            break

    else:
        response_text_output = "Warning: Maximum iterations reached without a final response."
        if is_verbose_mode: print(response_text_output)

    return response_text_output