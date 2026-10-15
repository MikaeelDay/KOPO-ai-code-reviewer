from pathlib import Path
import subprocess
import sys
import os
import typer
from ollama import chat
from .llm import stream_answer


TIMEOUT = 10
EXIT_WORDS = {"exit", "quit", "q", "no", "n"}

SYSTEM_PROMPT = """
You are KOPO (it does not stand for anything if user asked), your name is KOPO if user asks an expert Python code reviewer and teacher.
You get a code, an execution status, stdout and stderr.

If status is SUCCESS, answer in this structure:
1. Overview: what the program does and what problem it solves (2-3 sentences).
2. Functions: list EVERY function or class in the code by its exact name. For each one explain
   what it does, what inputs it takes and what it returns.
3. How it works: explain the main flow or algorithm step by step.
4. Result: explain the stdout and say whether it is correct. State clearly that the code works.

If status is FAILED, answer in this structure:
1. Error: quote the last line of stderr.
2. Cause: explain in detail why this error happens.
3. Fix: show the corrected lines of code and explain why the fix works.

Rules:
- Only describe functions and variables that really exist in the code. Never invent any.
- Never mention errors that are not in stderr.
- For follow-up questions, answer clearly and in enough detail for the user to understand.
"""



def resolve_path(name):
    """Accept both 'test' and 'test.py'."""
    path = Path(name)
    if path.suffix != ".py":
        path = path.with_suffix(".py")
    return path


def get_output(path):
    """Run the file and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT,
            stdin=subprocess.DEVNULL,  # input() fails instead of hanging
        )
    except subprocess.TimeoutExpired:
        return -1, "", f"TimeoutExpired: the code ran longer than {TIMEOUT} seconds"

    # print("--- DEBUG ---")
    # print("returncode:", result.returncode)
    # print("stderr:", result.stderr)
    # print("--- END ---")
    return result.returncode, result.stdout, result.stderr





def main():
    if len(sys.argv) < 2:
        typer.secho("Error: no file given.", fg=typer.colors.RED)
        raise SystemExit(1)

    path = resolve_path(sys.argv[1])

    if not path.exists():
        typer.secho(f"Error: {path} not found.", fg=typer.colors.RED)
        raise SystemExit(1)

    file_content = path.read_text(encoding="utf-8")

    print("checking your code...")
    returncode, stdout, stderr = get_output(path)
    status = "FAILED" if returncode != 0 else "SUCCESS"

    try:
        compile(file_content, str(path), "exec")
    except SyntaxError as e:
        typer.secho(f"Line {e.lineno}: {e.msg}", fg=typer.colors.RED)

    user_input = f"""Code:
{file_content}

Execution status: {status}
stdout:
{stdout or "(empty)"}
stderr:
{stderr or "(empty)"}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    # First analysis of the code
    answer = stream_answer(messages)
    messages.append({"role": "assistant", "content": answer})

    # Follow-up questions
    while True:
        prompt = typer.style(
            "\nDo you have another question about this code? (type 'exit' to quit)\n> ",
            fg=typer.colors.CYAN,
        )
        question = input(prompt).strip()

        if not question:
            continue
        if question.lower() in EXIT_WORDS:
            break

        messages.append({"role": "user", "content": question})
        answer = stream_answer(messages)
        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        typer.secho("\nCancelled by user.", fg=typer.colors.YELLOW)
        raise SystemExit(130)