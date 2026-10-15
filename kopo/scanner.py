import os
from pathlib import Path



IGNORED_DIRS = {
    ".kopo", ".git", "__pycache__", "venv", ".venv", "env",
    "node_modules", ".idea", ".vscode", "site-packages", "build", "dist",
}


def collect_python_files(root: Path):
    """Walk through root and all sub-folders and return every .py file."""
    files = []
    for folder, dirs, names in os.walk(root):
        # Editing `dirs` in place tells os.walk not to enter ignored folders
        dirs[:] = sorted(
            d for d in dirs
            if d not in IGNORED_DIRS and not d.endswith(".egg-info")
        )
        for name in sorted(names):
            if name.endswith(".py"):
                files.append(Path(folder) / name)
    return files


def save_project_code(root: Path):
    """Write the code of all .py files into .kopo/project_code.txt.

    Every file's code is preceded by a header with its relative path.
    """
    files = collect_python_files(root)
    output = root / ".kopo" / "project_code.txt"

    parts = []
    for path in files:
        relative = path.relative_to(root).as_posix()
        code = path.read_text(encoding="utf-8", errors="replace")
        header = f"{'=' * 60}\nFILE: {relative}\n{'=' * 60}"
        parts.append(f"{header}\n{code.rstrip()}\n")

    output.write_text("\n".join(parts), encoding="utf-8")
    return files, output