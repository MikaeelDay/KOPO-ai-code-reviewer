# KOPO

**A local, privacy-friendly AI code reviewer and project assistant for Python, powered by [Ollama](https://ollama.com).**

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Runs locally](https://img.shields.io/badge/LLM-runs%20locally-informational)

KOPO is a command-line tool that lives inside your project folder, just like `git`. Run it on a single Python file to get an explanation of what the code does and why it fails, or open a chat with it to ask questions about your whole project. It reads your files, works out how they import each other, and gives the language model only the code that matters for your question.

Everything runs on your own machine through Ollama, so with a default local Ollama installation your code never leaves your computer.

---

## Features

- **File review (`kopo rv`)**: runs a Python file (with a timeout), captures `stdout`, `stderr` and the exit status, checks the syntax, and asks the model to explain the code or the error. You can keep chatting about that file afterwards.
- **Project chat (`kopo ask`)**: an interactive Q&A session about your whole project. Start it empty, or pass the first question directly.
- **Project scanning (`kopo init` / `kopo scan`)**: finds every `.py` file in the project (skipping `venv`, `.git`, `__pycache__`, `node_modules`, and similar folders) and saves all code into a single text file with the file name above each block.
- **Dependency map**: uses Python's `ast` module to find which file imports which, resolving both absolute and relative imports, and writes an "imports / used by" map for the whole project.
- **Smart context selection**: when you ask about a file, KOPO sends that file plus the files it imports, within a size budget, instead of dumping the entire project into a small model.
- **Streaming output** with colors, and a clean `Ctrl+C`.

## How it works

```
                      kopo init / kopo scan
                               |
           +-------------------+-------------------+
           v                                       v
   .kopo/project_code.txt                 .kopo/project_map.txt
   (all code, file name headers)          (imports / used by, via ast)

   kopo ask "how does views.py work?"
        |
        |-- pick files named in the question (+ the files they import)
        |-- build a context within a size limit
        '-- stream the answer from the local model (Ollama)

   kopo rv my_script
        |
        |-- run the file (10 s timeout), capture stdout / stderr / exit code
        |-- check the syntax with compile()
        '-- ask the model to explain the code or the error
```

## Requirements

- Python 3.10 or newer recommended (developed and tested on Python 3.12)
- [Ollama](https://ollama.com/download) installed and running
- A pulled model. KOPO uses `qwen2.5:0.5b` by default:

```bash
ollama pull qwen2.5:0.5b
```

## Installation

KOPO is not on PyPI yet, so install it from source:

```bash
git clone https://github.com/MikaeelDay/KOPO-ai-code-reviewer.git
cd KOPO-ai-code-reviewer
pip install -e .
```

Check that it works:

```bash
kopo --help
```

> **Windows note:** if `kopo` is "not recognized" after installation, the Python `Scripts` folder is not in your `PATH`. `pip show -f kopo` tells you where `kopo.exe` was installed. Alternatively, install with [pipx](https://pipx.pypa.io), which manages `PATH` for you: `pipx install .`

## Quick start

```bash
cd path/to/your/python/project
kopo init                 # one-time setup for this project
kopo ask                  # chat about the project
kopo rv my_script         # review a single file ('.py' is optional)
```

`kopo init` creates a `.kopo/` folder in the project. Like `.git`, KOPO looks for it in the current folder and its parents, so commands work from any sub-folder. Outside an initialized project, KOPO refuses to run and tells you to run `kopo init` first.

## Commands

| Command | What it does |
|---|---|
| `kopo init` | Initializes KOPO in the current folder, scans all Python files, and writes the code and dependency map into `.kopo/`. |
| `kopo scan` | Re-reads all Python files. Run it after your code changes, so the saved map is up to date. |
| `kopo rv <file>` | Runs the file, checks it, and lets the model explain the code or the error. Then opens a follow-up Q&A. Accepts `test` or `test.py`. |
| `kopo ask [question]` | Opens an interactive chat about the project. An optional first question starts the conversation. Type `exit` to leave. |
| `kopo lst` | Lists the files and folders of the current directory. |

### Example: reviewing a file

```text
$ kopo rv test
checking your code...
KOPO:
1. Overview: The program builds a graph representing a road network and calculates
   the shortest distances and routes from a starting city to all other cities.
2. Functions:
   - `build_graph()`: Builds the graph with cities as nodes and roads as edges.
   - `shortest_paths(graph, start)`: Uses Dijkstra's algorithm to find the shortest
     distances and routes from the start city to all other cities.
   ...

Do you have another question about this code? (type 'exit' to quit)
> exit
```

### Example: chatting about a project

```text
$ kopo ask
KOPO project chat. Ask anything about your code (type 'exit' to quit).

> how does views.py work
Files: questions/views.py, questions/forms.py, questions/models.py
KOPO:
...
```

The `Files:` line shows exactly which files the model was given, so you can tell whether a bad answer came from the file selection or from the model.

### Example: the dependency map

`.kopo/project_map.txt` is plain text and easy to read:

```text
questions/forms.py
  imports: questions/models.py
  used by: questions/views.py

questions/models.py
  imports: -
  used by: questions/admin.py, questions/forms.py, questions/signals.py, questions/views.py
```

## Project layout

```text
kopo/
├── cli.py          # CLI commands (Typer): init, scan, rv, lst, ask
├── reviewer.py     # single-file review flow
├── assistant.py    # project chat flow
├── context.py      # choosing relevant files and building the model context
├── project_map.py  # import analysis with ast, dependency map
├── scanner.py      # finding Python files, saving all code to one text file
├── project.py      # finding the .kopo project root
├── runner.py       # running a file with a timeout
├── llm.py          # streaming answers from Ollama (model name lives here)
├── prompts.py      # system prompts
└── constants.py
```

## Configuration

There is no config file yet. For now, the main settings are constants in the code:

| Setting | Where | Default |
|---|---|---|
| Model | `MODEL` in `kopo/llm.py` | `qwen2.5:0.5b` |
| Context window | `num_ctx` in `kopo/llm.py` | `8192` |
| Run timeout for `kopo rv` | `TIMEOUT` in `kopo/runner.py` | `10` seconds |
| Ignored folders | `IGNORED_DIRS` in `kopo/scanner.py` | `.git`, `venv`, `.venv`, `env`, `__pycache__`, `node_modules`, ... |
| Context size for `kopo ask` | `limit` in `build_context` (`kopo/context.py`) | 12,000 characters |

To use a bigger model, pull it and change `MODEL`, for example:

```bash
ollama pull qwen2.5-coder:3b
```

## Safety

- **`kopo rv` executes the file you give it** on your machine, with a 10-second timeout and no keyboard input. Only review code you trust.
- `kopo ask`, `kopo scan` and `kopo init` only read your files. They never run your code.
- With a default local Ollama setup, no code is sent to an external service.

## Known limitations

KOPO is an early version (v0.1.0). Please keep these in mind:

- **Small model, small brain.** The default `qwen2.5:0.5b` is fast but weak. It can miss functions, repeat itself, or invent details. A larger model such as `qwen2.5-coder:3b` gives noticeably better answers.
- **Python only.** Other languages are ignored.
- **The dependency map follows `import` statements only.** Links that frameworks create with strings, such as Django's `include("app.urls")` or `INSTALLED_APPS`, are not detected yet.
- **Follow-up questions need file names.** A follow-up such as "tell me more about it" has no file name in it, so KOPO falls back to the project overview instead of the previous file.
- **Large files are truncated** to fit the context budget.
- **Tested mainly on Windows.**

## Roadmap

Ideas for the next versions:

- A config file inside `.kopo/` (model, timeout, ignored folders) and command-line options such as `--model` and `--no-run`
- Remembering the last selected files for follow-up questions
- Detecting framework wiring (Django URL includes, installed apps) in the dependency map
- Automated tests and CI
- Publishing to PyPI

## Contributing

Issues and pull requests are welcome. If you report a bad answer, please include the command you ran, the `Files:` line KOPO printed, and the model you used.

## License

MIT. See [LICENSE](LICENSE).

## Author

Built by [Mikaeel Raeisi](https://github.com/MikaeelDay).