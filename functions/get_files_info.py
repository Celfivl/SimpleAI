import os
from functions import config
from google.genai import types

def get_files_info(working_directory, directory="."):
    abs_working_dir = os.path.abspath(working_directory)
    target_dir = os.path.abspath(os.path.join(working_directory, directory))
    if not target_dir.startswith(abs_working_dir):
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'
    if not os.path.isdir(target_dir):
        return f'Error: "{directory}" is not a directory'
    try:
        files_info = []
        for filename in os.listdir(target_dir):
            filepath = os.path.join(target_dir, filename)
            file_size = 0
            is_dir = os.path.isdir(filepath)
            file_size = os.path.getsize(filepath)
            files_info.append(
                f"- {filename}: file_size={file_size} bytes, is_dir={is_dir}"
            )
        return "\n".join(files_info)
    except Exception as e:
        return f"Error listing files: {e}"
    
def get_file_content(working_directory, file_path):
    """
    Reads the content of a file located within the specified working directory,
    with security checks and basic error handling.
    """
    abs_working_dir = os.path.abspath(working_directory)
    full_file_path = os.path.abspath(os.path.join(working_directory, file_path))

    # 1. Path validation: Check if file_path is outside the working_directory.
    if not full_file_path.startswith(abs_working_dir):
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

    # 2. File type check: Ensure the path points to a regular file.
    if not os.path.isfile(full_file_path):
        return f'Error: File not found or is not a regular file: "{file_path}"'

    content = ""
    try:
        with open(full_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Truncate if content is longer than the defined limit
        if len(content) > config.MAX_FILE_READ_CHARS:
            content = content[:config.MAX_FILE_READ_CHARS] + \
                      f'[...File "{file_path}" truncated at {config.MAX_FILE_READ_CHARS} characters]'
        return content
    
    except FileNotFoundError:
        # This case should be largely prevented by the os.path.isfile check above,
        # but included for extreme robustness (e.g., file deleted between checks).
        return f"Error: File '{file_path}' not found."
    except PermissionError:
        # Handles cases where the program lacks necessary read permissions.
        return f"Error: Permission denied to read file '{file_path}'."
    except UnicodeDecodeError:
        # Catches errors when trying to read a non-UTF-8 encoded file (e.g., binary files).
            return f"Error: Could not decode file '{file_path}'. It might not be a text file or uses an unsupported encoding."
    except Exception as e:
            # Catches any other unexpected errors during the file reading process.
            return f"Error: An unexpected error occurred while reading '{file_path}': {e}"
    
def write_file(working_directory, file_path, content):
    try:
        # 1. Normalize and resolve paths for security
        abs_working_dir = os.path.abspath(working_directory)
        abs_file_path = os.path.abspath(os.path.join(abs_working_dir, file_path))
    
        # Ensure the file_path is within the working_directory
        # os.path.commonprefix is a bit unreliable as it works character-by-character.
        # A more robust check is to ensure that the resolved file path starts with the resolved working directory path
        if not abs_file_path.startswith(abs_working_dir):
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'
    
        # 2. Ensure the directory for the file exists, creating it if necessary.
        # os.makedirs(..., exist_ok=True) handles the case where directories already exist,
        # preventing FileExistsError.
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
    
        # 3. Overwrite the contents of the file
        with open(abs_file_path, 'w') as f:
            f.write(content)
    
        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    
    except OSError as e:
            # Catch OS-related errors like permission issues or invalid paths.
            return f"Error: An OS error occurred while writing to \"{file_path}\": {e}"
    except Exception as e:
            # Catch any other unexpected errors
        return f"Error: An unexpected error occurred while writing to \"{file_path}\": {e}"

schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)

# --- Schema for get_file_content ---
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Reads the content of a specified file, constrained to the working directory. Returns the file's content or an error.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to read, relative to the working directory. Must be a regular file.",
            ),
        },
        required=["file_path"],
    ),
)

# --- Schema for run_python_file ---
schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python script securely within the working directory. Returns the script's stdout, stderr, and exit code, or an error.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python script to execute, relative to the working directory. Must be a .py file.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                description="Optional: A list of string arguments to pass to the Python script.",
                items=types.Schema(type=types.Type.STRING),
            ),
        },
        required=["file_path"],
    ),
)

# --- Schema for write_file ---
schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes content to a file within the working directory. Creates the file if it doesn't exist and overwrites if it does. Returns a success or error message.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to write, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content string to write into the file.",
            ),
        },
        required=["file_path", "content"],
    ),
)