import os
from functions.get_files_info import get_file_content

# --- First Test: lorem.txt truncation ---
print("--- Testing lorem.txt truncation ---")
try:
    lorem_content = get_file_content("calculator", "lorem.txt")
    print(f"Content of lorem.txt: {lorem_content}")
    # You'll need to manually inspect the output to see if it truncates properly
    # If the assignment specifies an exact truncation length, you could compare against it.
    # Otherwise, simply observing the output is sufficient for this stage.
except FileNotFoundError:
    print("Error: lorem.txt not found in the 'calculator' directory.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
