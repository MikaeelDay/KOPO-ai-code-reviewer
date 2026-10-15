import ast
from pathlib import Path

from .scanner import collect_python_files


def extract_imports(path):
    """Return a list of (module_name, level) for every import in the file."""
    source = Path(path).read_text(encoding="utf-8", errors="replace")

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, 0))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.level))
            else:
                for alias in node.names:
                    imports.append((alias.name, node.level))

    return imports

def module_name(path, root):
    parts = list(Path(path).relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def package_of(path, root):
    name = module_name(path, root)
    if Path(path).name == "__init__.py":
        return name
    return name.rpartition(".")[0]


def resolve_import(module, level, path, root, module_map):
    if level == 0:
        target = module
    else:
        package = package_of(path, root)
        parts = package.split(".") if package else []
        parts = parts[: max(0, len(parts) - (level - 1))]
        target = ".".join(parts + [module])

    pieces = target.split(".")
    while pieces:
        name = ".".join(pieces)
        if name in module_map:
            return module_map[name]
        pieces.pop()
    return None


def build_dependency_map(files, root):
    module_map = {}
    for f in files:
        name = module_name(f, root)
        if name:
            module_map[name] = f

    graph = {}
    for path in files:
        deps = set()
        for module, level in extract_imports(path):
            target = resolve_import(module, level, path, root, module_map)
            if target is not None and target != path:
                deps.add(target)
        graph[path] = deps
    return graph


def save_project_map(root):
    root = Path(root)
    files = collect_python_files(root)
    graph = build_dependency_map(files, root)

    # Reverse direction: for each file, who imports it?
    used_by = {path: set() for path in files}
    for path, deps in graph.items():
        for dep in deps:
            used_by[dep].add(path)

    def rel(p):
        return p.relative_to(root).as_posix()

    lines = []
    for path in files:
        imports = sorted(rel(d) for d in graph[path])
        users = sorted(rel(u) for u in used_by[path])

        if not imports and not users:
            continue  # isolated file, nothing to show

        lines.append(rel(path))
        lines.append("  imports: " + (", ".join(imports) or "-"))
        lines.append("  used by: " + (", ".join(users) or "-"))
        lines.append("")

    output = root / ".kopo" / "project_map.txt"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output