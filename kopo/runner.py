import subprocess
import sys

TIMEOUT = 10


def get_output(path):
    """Run the file and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return -1, "", f"TimeoutExpired: the code ran longer than {TIMEOUT} seconds"

    return result.returncode, result.stdout, result.stderr