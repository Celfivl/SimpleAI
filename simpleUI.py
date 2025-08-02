import tkinter as tk
from tkinter import ttk, filedialog, messagebox # Added filedialog and messagebox
import sys
import os
import datetime

# Adjust sys.path to ensure main.py is importable
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from main import run_ai_query

class AssistantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sophisticated AI Assistant")
        self.geometry("1000x900")  # Even larger default size
        self.configure(bg="#263238")  # Dark Blue Grey Background

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.style.configure('.', foreground="#ECEFF1", background="#263238")
        self.style.configure('TFrame', background="#263238")
        self.style.configure('TLabel', foreground="#BBDEFB", background="#263238", font=("Arial", 10, "bold"))
        self.style.configure('TButton', foreground="#FFFFFF", background="#37474F", font=("Arial", 10, "bold"))
        self.style.map('TButton', background=[('active', '#546E7A'), ('pressed', '#37474F')])
        self.style.configure('TCheckbutton', foreground="#BBDEFB", background="#263238")

        # Make window resizable - Adjusted row configurations
        self.grid_rowconfigure(0, weight=0) # Top Control Bar Frame
        self.grid_rowconfigure(1, weight=0) # History Label
        self.grid_rowconfigure(2, weight=3) # History field
        self.grid_rowconfigure(3, weight=0) # Input Label
        self.grid_rowconfigure(4, weight=1) # Input field
        self.grid_rowconfigure(5, weight=0) # Response Label
        self.grid_rowconfigure(6, weight=2) # Response field
        self.grid_columnconfigure(0, weight=1)

        self.conversation_messages = []

        self.verbose_var = tk.BooleanVar(value=False) 

        self._create_widgets()
        self.input_field.focus_set()

        self.bind('<Return>', self._send_request_event)

        self.conversation_history_field.tag_config('user', foreground="#90CAF9", font=("Arial", 9, "bold"))
        self.conversation_history_field.tag_config('ai', foreground="#BBDEFB", font=("Arial", 9))
        self.conversation_history_field.tag_config('delimiter', foreground="#607D8B", font=("Arial", 8))

    # --- New Helper Methods ---

    def _save_history(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.conversation_history_field.get("1.0", tk.END))
            messagebox.showinfo("History Saved", f"Conversation history saved to:\n{file_path}")

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the conversation history?"):
            self.conversation_history_field.config(state=tk.NORMAL)
            self.conversation_history_field.delete("1.0", tk.END)
            self.conversation_history_field.config(state=tk.DISABLED)
            self.conversation_messages = [] # Clear the internal message list as well
            messagebox.showinfo("History Cleared", "Conversation history has been cleared.")

    def _confirm_tool_call(self, function_name, function_args):
        # Create a detailed message for the user to review
        confirmation_message = (
            f"The AI proposes to call the function:\n\n"
            f"Function: {function_name}\n"
            f"Arguments:\n"
        )
        for arg, value in function_args.items():
            confirmation_message += f"  - {arg}: {value}\n"
        confirmation_message += "\nDo you approve this action?"

        # Show a confirmation dialog
        return messagebox.askyesno("Approve Tool Call", confirmation_message)
    
    def _create_widgets(self):
        # --- New: Top Control Bar Frame ---
        top_control_bar_frame = ttk.Frame(self, padding="10 5 10 5") # Padding for top bar
        top_control_bar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5,0))
        # Configure columns to push buttons to the right
        top_control_bar_frame.grid_columnconfigure(0, weight=1) # Empty column to push buttons right
        top_control_bar_frame.grid_columnconfigure(1, weight=0) # Save History Button
        top_control_bar_frame.grid_columnconfigure(2, weight=0) # Clear History Button
        top_control_bar_frame.grid_columnconfigure(3, weight=0) # Verbose Checkbox


        self.save_history_button = ttk.Button(top_control_bar_frame, text="Save History", command=self._save_history)
        self.save_history_button.grid(row=0, column=1, sticky="e", padx=(0,5))

        self.clear_history_button = ttk.Button(top_control_bar_frame, text="Clear History", command=self._clear_history)
        self.clear_history_button.grid(row=0, column=2, sticky="e", padx=(5,10))

        # This assumes verbose_var is defined in __init__
        self.verbose_checkbox = ttk.Checkbutton(top_control_bar_frame, text="Verbose Output", variable=self.verbose_var)
        self.verbose_checkbox.grid(row=0, column=3, sticky="e", padx=(0,10))


        # Conversation History Label (now in row 1)
        self.history_label = ttk.Label(self, text="Conversation History:")
        self.history_label.grid(row=1, column=0, sticky="w", padx=10, pady=(10, 0))

        # Conversation History Frame (now in row 2)
        history_frame = ttk.Frame(self, padding="10 10 10 0")
        history_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)

        history_text_frame = ttk.Frame(history_frame)
        history_text_frame.grid(row=0, column=0, sticky="nsew")
        history_text_frame.grid_rowconfigure(0, weight=1)
        history_text_frame.grid_columnconfigure(0, weight=1)

        self.conversation_history_field = tk.Text(history_text_frame, height=15, width=75, wrap=tk.WORD, state=tk.DISABLED, bg="#37474F", fg="#ECEFF1", font=("Arial", 9))
        self.conversation_history_field.grid(row=0, column=0, sticky="nsew")

        history_scrollbar = ttk.Scrollbar(history_text_frame, command=self.conversation_history_field.yview)
        history_scrollbar.grid(row=0, column=1, sticky="ns")
        self.conversation_history_field.config(yscrollcommand=history_scrollbar.set)

        # Input Label (now in row 3)
        self.input_label = ttk.Label(self, text="Your Request:")
        self.input_label.grid(row=3, column=0, sticky="w", padx=10, pady=(10, 0))

        # Input Frame (now in row 4)
        input_frame = ttk.Frame(self, padding="10 10 10 0")
        input_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        input_frame.grid_rowconfigure(0, weight=1)
        input_frame.grid_columnconfigure(0, weight=1)

        input_text_frame = ttk.Frame(input_frame)
        input_text_frame.grid(row=0, column=0, sticky="nsew")
        input_text_frame.grid_rowconfigure(0, weight=1)
        input_text_frame.grid_columnconfigure(0, weight=1)

        self.input_field = tk.Text(input_text_frame, height=5, width=75, wrap=tk.WORD, font=("Arial", 10), bg="#455A64", fg="#ECEFF1")
        self.input_field.grid(row=0, column=0, sticky="nsew")

        input_scrollbar = ttk.Scrollbar(input_text_frame, command=self.input_field.yview)
        input_scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_field.config(yscrollcommand=input_scrollbar.set)

        # Send Button (Moved into Input Frame to be below input field, expanded)
        self.send_button = ttk.Button(input_frame, text="Send Request", command=self._send_request)
        self.send_button.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5,0))

        # Output Label (now in row 5)
        self.output_label = ttk.Label(self, text="Current AI Response:")
        self.output_label.grid(row=5, column=0, sticky="w", padx=10, pady=(10, 0))

        # Output Frame (now in row 6)
        output_frame = ttk.Frame(self, padding="10 10 10 10")
        output_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=5)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        output_text_frame = ttk.Frame(output_frame)
        output_text_frame.grid(row=0, column=0, sticky="nsew")
        output_text_frame.grid_rowconfigure(0, weight=1)
        output_text_frame.grid_columnconfigure(0, weight=1)

        self.output_field = tk.Text(output_text_frame, height=10, width=75, state=tk.DISABLED, wrap=tk.WORD, bg="#455A64", fg="#ECEFF1", font=("Arial", 10))
        self.output_field.grid(row=0, column=0, sticky="nsew")

        output_scrollbar = ttk.Scrollbar(output_text_frame, command=self.output_field.yview)
        output_scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_field.config(yscrollcommand=output_scrollbar.set)
        
    def _append_to_history(self, role, text):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.conversation_history_field.config(state=tk.NORMAL)
        if self.conversation_history_field.index(tk.END) != "1.0\n":
            self.conversation_history_field.insert(tk.END, "\n")

        if role == "user":
            prefix = f"[{timestamp}] You:\n"
            self.conversation_history_field.insert(tk.END, prefix, 'user')
            self.conversation_messages.append({"role": "user", "text": text})
        else: # role == "ai"
            separator = "*" * 50 + "\n"
            self.conversation_history_field.insert(tk.END, separator, 'delimiter')
            prefix = f"[{timestamp}] AI:\n"
            self.conversation_history_field.insert(tk.END, prefix, 'ai')
            self.conversation_messages.append({"role": "ai", "text": text})

        self.conversation_history_field.insert(tk.END, text + "\n", role)
        self.conversation_history_field.config(state=tk.DISABLED)
        self.conversation_history_field.yview(tk.END)

    def _display_output(self, text, state=tk.NORMAL):
        self.output_field.config(state=tk.NORMAL)
        self.output_field.delete("1.0", tk.END)
        self.output_field.insert(tk.END, text)
        self.output_field.config(state=state)

    def _send_request(self):
        user_input = self.input_field.get("1.0", tk.END).strip()
        if not user_input:
            self._display_output("Please enter a prompt.")
            return

        self._display_output("Thinking...\n", state=tk.DISABLED)
        self.input_field.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
        # Add disable for history buttons while AI is processing
        self.save_history_button.config(state=tk.DISABLED)
        self.clear_history_button.config(state=tk.DISABLED)
        self.update_idletasks()

        self._append_to_history("user", user_input)
        self.input_field.delete("1.0", tk.END)

        is_verbose_mode = self.verbose_var.get()
        final_ai_response = run_ai_query(user_input, is_verbose_mode) # This will be modified for tool confirmation

        self._display_output(final_ai_response)
        self._append_to_history("ai", final_ai_response)

        self.input_field.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
        self.save_history_button.config(state=tk.NORMAL) # Re-enable buttons
        self.clear_history_button.config(state=tk.NORMAL)
        self.input_field.focus_set()

    def _send_request_event(self, event=None):
        self._send_request()

if __name__ == "__main__":
    app = AssistantApp()
    app.mainloop()