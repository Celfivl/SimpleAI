# tests.py
import sys
import os

# Ensure the 'functions' directory is in the Python path
# This allows importing modules directly from it.
sys.path.append('functions')

# Import the new run_python_file function
from run_python import run_python_file 

# --- Test Cases for run_python_file ---

print("--- Testing run_python_file functionality ---")

# Test Case 1: Reading an existing file (should print calculator usage)
print("\nTest 1: Running 'main.py' in 'calculator' (should print usage instructions)")
result1 = run_python_file("calculator", "main.py")
print(result1)

# Test Case 2: Running the calculator with arguments (should run the calculation)
print("\nTest 2: Running 'main.py' with arguments '3 + 5' (should show calculation result)")
result2 = run_python_file("calculator", "main.py", ["3 + 5"])
print(result2)

# Test Case 3: Running the tests.py file itself
print("\nTest 3: Running 'tests.py' in 'calculator' (should execute this test file again)")
result3 = run_python_file("calculator", "tests.py")
print(result3)

# Test Case 4: Path traversal security check (should return an error)
print("\nTest 4: Attempting path traversal with '../main.py' (should return an error)")
result4 = run_python_file("calculator", "../main.py")
print(result4)

# Test Case 5: File not found error (should return an error)
print("\nTest 5: Attempting to run a non-existent file 'nonexistent.py' (should return an error)")
result5 = run_python_file("calculator", "nonexistent.py")
print(result5)

print("\n--- All run_python_file tests complete ---")