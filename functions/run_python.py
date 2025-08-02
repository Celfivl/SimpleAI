# functions/run_python.py
import os
import subprocess
import sys # To get the Python executable path

def run_python_file(working_directory, file_path, args=[]):
    """
    Performs initial validation checks before executing a Python file
    and then executes it using subprocess.run.

    Args:
        working_directory (str): The base directory where file operations are permitted.
        file_path (str): The path to the Python script relative to the working_directory.
        args (list): A list of command-line arguments to pass to the Python script.

    Returns:
        str: A formatted string containing the script's output, errors, or an error message.
    """
    # Initial validation checks from the previous step
    abs_working_dir = os.path.abspath(working_directory)
    full_file_path = os.path.join(abs_working_dir, file_path)
    abs_file_path = os.path.abspath(full_file_path)

    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

    if not os.path.exists(abs_file_path):
        return f'Error: File "{file_path}" not found.'

    if not file_path.endswith(".py"):
        return f'Error: "{file_path}" is not a Python file.'

    # --- Subprocess execution ---
    try:
        # Construct the command to execute
        # Using sys.executable ensures the same Python interpreter is used.
        command = [sys.executable, abs_file_path] + args

        # Execute the Python script using subprocess.run
        # shell=False is crucial for security.
        # capture_output=True captures stdout and stderr.
        # text=True decodes output as strings.
        # timeout sets the maximum execution time.
        process = subprocess.run(
            command,
            cwd=abs_working_dir,  # Set the working directory for the subprocess
            capture_output=True,
            text=True,
            timeout=30, # Set timeout to 30 seconds
            check=False # Do not raise CalledProcessError automatically
        )

        # Format the output
        output_parts = []

        if process.stdout:
            output_parts.append(f"STDOUT:\n{process.stdout}")

        if process.stderr:
            output_parts.append(f"STDERR:\n{process.stderr}")

        if process.returncode != 0:
            output_parts.append(f"Process exited with code {process.returncode}")

        if not output_parts: # If both stdout and stderr are empty and exit code is 0
            return "No output produced."
        else:
            return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        # The process was killed due to timeout
        return f"Error: execution timed out after 30 seconds."
    except Exception as e:
        # Catch any other exceptions during execution
        return f"Error: executing Python file: {e}"