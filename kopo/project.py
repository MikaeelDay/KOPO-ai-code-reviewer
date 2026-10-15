from pathlib import Path
import typer

def find_kopo_root():
    """Look for .kopo in the current folder and its parents."""
    current = Path.cwd()
    for folder in [current, *current.parents]:
        if (folder / ".kopo").is_dir():
            return folder
    return None


def require_init():
    root = find_kopo_root()
    if root is None:
        typer.secho("Error: not a KOPO project. Run 'kopo init' first.",fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    return root