import os
import config

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