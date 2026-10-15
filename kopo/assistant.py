import typer

from .constants import EXIT_WORDS
from .context import build_context, select_relevant_files
from .llm import stream_answer
from .project_map import build_dependency_map, save_project_map
from .prompts import PROJECT_SYSTEM_PROMPT
from .scanner import collect_python_files


def build_question_message(question, root, files, graph):
    selected = select_relevant_files(question, files, graph, root)

    if selected:
        context, used = build_context(selected, root)
        label = "Code of the relevant files"
    else:
        map_path = root / ".kopo" / "project_map.txt"
        if not map_path.exists():
            save_project_map(root)
        file_list = "\n".join(p.relative_to(root).as_posix() for p in files)
        context = (
            f"All Python files:\n{file_list}\n\n"
            f"Dependency map:\n{map_path.read_text(encoding='utf-8')}"
        )
        used = []
        label = "Project overview"

    return f"{label}:\n{context}\n\nQuestion: {question}", used


def ask_project(question, root):
    history = []

    if not question:
        typer.secho(
            "KOPO project chat. Ask anything about your code (type 'exit' to quit).",
            fg=typer.colors.GREEN,
            bold=True,
        )

    while True:
        # Ask for the next question if we don't have one yet
        while not question:
            question = input(typer.style("\n> ", fg=typer.colors.CYAN)).strip()

        if question.lower() in EXIT_WORDS:
            break

        # Re-read the project every time, so code you edit during the chat is seen
        files = collect_python_files(root)
        if not files:
            typer.secho("No Python files found in this project.", fg=typer.colors.YELLOW)
            break
        graph = build_dependency_map(files, root)

        message, used = build_question_message(question, root, files, graph)
        if used:
            names = ", ".join(p.relative_to(root).as_posix() for p in used)
            typer.secho(f"Files: {names}", fg=typer.colors.CYAN)

        messages = (
            [{"role": "system", "content": PROJECT_SYSTEM_PROMPT}]
            + history
            + [{"role": "user", "content": message}]
        )
        answer = stream_answer(messages)

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        question = ""