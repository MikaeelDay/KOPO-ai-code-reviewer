from pathlib import Path
from ollama import chat
import subprocess
import sys


def convert_to_txt(source, destination):
    source = Path(source)
    destination = Path(destination)

    destination.write_bytes(source.read_bytes())


def get_output(code):
    result = subprocess.run(
        [sys.executable, code],
        capture_output=True,
        text=True
    )

    if result.stdout:
        return result.stdout

    if result.stderr:
        return result.stderr


FILE_NAME = input('What file you want to check?(write name file for example myfile) :')

convert_to_txt(f'{FILE_NAME}.py', f'{FILE_NAME}.txt')

with open(f'{FILE_NAME}.txt', 'r') as f:
    code_file = f.read()

FILE_OUTPUT = get_output(f'{FILE_NAME}.py')
print(FILE_OUTPUT)

messages = [
    {
        "role": "system",
        "content": """
You are a Python code reviewer.

Follow these rules strictly:
1. Explain briefly what the code does.
2. Check the actual execution output and errors.
3. Do not invent errors that are not present.
4. If the code runs correctly, say that it works correctly.
5. If there is a SyntaxError, explain the exact cause and how to fix it.
6. Do not rewrite or improve the code unless necessary to fix a real error.
7. Answer briefly.
"""
    }
]

print("Chatbot started!")

user_input = \
    f"""
        read this python code: {code_file} and tell me what it does,and this is output: {FILE_OUTPUT}
        , if output contains syntax error, read output and tell me how to fix it,
        and if output does not contain syntax error just leave to output and talk about code

        """
while True:

    if user_input.lower() == "exit":
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = chat(
        model="qwen2.5:0.5b",
        messages=messages
    )

    answer = response.message.content

    print(f"Bot: {answer}\n")

    messages.append({
        "role": "assistant",
        "content": answer
    })
    break
