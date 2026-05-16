import os
from pathlib import Path


def _load_dotenv(file_name=".env"):
    env_path = Path(__file__).resolve().parent / file_name

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


_load_dotenv()


def get_env(name, default=None):
    return os.getenv(name, default)
