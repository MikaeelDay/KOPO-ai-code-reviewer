from pathlib import Path
import subprocess
import sys

import typer

from .project import require_init
from .scanner import save_project_code
from .project_map import save_project_map
from .assistant import ask_project
from typing import Optional

app = typer.Typer()


@app.command()
def init():
    root = Path.cwd()
    (root / ".kopo").mkdir(exist_ok=True)

    files, output = save_project_code(root)
    save_project_map(root)

    typer.secho(f"KOPO initialized in {root}", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Found {len(files)} Python file(s) -> {output}")


@app.command()
def scan():
    """Re-read all Python files (use this after your code changes)."""
    root = require_init()
    files, output = save_project_code(root)
    save_project_map(root)

    typer.secho(f"Scanned {len(files)} Python file(s)", fg=typer.colors.GREEN)
    for path in files:
        typer.echo(f"  {path.relative_to(root).as_posix()}")

@app.command()
def rv(filename: str):
    root = require_init()
    target = Path(filename).resolve()
    subprocess.run([sys.executable, "-m", "kopo.check_file", str(target)])

@app.command()
def lst():
    """List files and folders of the current directory."""
    require_init()
    cwd = Path.cwd()
    typer.echo(f"Files and directories in {cwd}:")

    for item in sorted(cwd.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        if item.name == ".kopo":
            continue
        if item.is_dir():
            typer.secho(f"{item.name}/", fg=typer.colors.BLUE, bold=True)
        else:
            typer.secho(item.name, fg=typer.colors.GREEN)

@app.command()
def ask(question: Optional[str] = typer.Argument(None)):
    """Chat with KOPO about the project (optionally start with a question)."""
    root = require_init()
    try:
        ask_project(question, root)
    except (KeyboardInterrupt, EOFError):
        typer.secho("\nCancelled by user.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=130)


if __name__ == "__main__":
    app()