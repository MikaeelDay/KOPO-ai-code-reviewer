import typer
from ollama import chat

MODEL = "qwen2.5:0.5b"


def stream_answer(messages, num_ctx=8192):
    """Stream the model's answer to the terminal and return the full text."""
    stream = chat(
        model=MODEL,
        messages=messages,
        stream=True,
        options={"temperature": 0, "seed": 42, "num_ctx": num_ctx},
    )

    typer.secho("KOPO:", fg=typer.colors.GREEN, bold=True)
    answer = ""
    for chunk in stream:
        piece = chunk.message.content
        print(piece, end="", flush=True)
        answer += piece
    print()
    return answer