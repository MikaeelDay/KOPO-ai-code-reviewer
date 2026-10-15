import re

def select_relevant_files(question, files, graph, root):
    text = question.lower()
    words = set(re.findall(r"[a-z_][a-z0-9_]*", text))

    selected = []
    for path in files:
        if path.stem == "__init__":
            continue
        rel = path.relative_to(root).as_posix().lower()
        if path.stem.lower() in words or rel in text:
            selected.append(path)

    # add what the selected files import (one level only)
    result = list(selected)
    for path in selected:
        for dep in sorted(graph[path]):
            if dep not in result:
                result.append(dep)

    return result

def build_context(paths, root, limit=12000):
    parts = []
    used = []
    total = 0

    for path in paths:
        rel = path.relative_to(root).as_posix()
        code = path.read_text(encoding="utf-8", errors="replace").rstrip()
        block = f"FILE: {rel}\n{code}\n"

        if total + len(block) > limit:
            remaining = limit - total
            if remaining < 500:
                break
            block = block[:remaining] + "\n... (truncated)\n"

        parts.append(block)
        used.append(path)
        total += len(block)

    return "\n".join(parts), used