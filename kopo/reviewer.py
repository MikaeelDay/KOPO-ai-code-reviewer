from pathlib import Path

import typer

from .llm import stream_answer
from .prompts import SYSTEM_PROMPT
from .runner import get_output
from .constants import EXIT_WORDS



def resolve_path(name):
    """Accept both 'test' and 'test.py'."""
    path = Path(name)
    if path.suffix != ".py":
        path = path.with_suffix(".py")
    return path


def review_file(filename):
    path = resolve_path(filename)

    if not path.exists():
        typer.secho(f"Error: {path} not found.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

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

    answer = stream_answer(messages)
    messages.append({"role": "assistant", "content": answer})

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