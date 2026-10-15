"""Container entrypoint (the runtime image has no shell, so read PORT here).

Also loads a local `.env` (if present) without overriding variables already set in the
environment, so `cp .env.example .env` + one key (AMD_TOKEN_FACTORY_API_KEY) is enough to go live.
"""

import os
from pathlib import Path

import uvicorn

DOTENV = Path(__file__).with_name(".env")


def load_dotenv(path: str | Path = DOTENV) -> None:
    """Minimal KEY=VALUE loader (no dependency). Real env vars win; blank lines and # comments skipped."""
    p = Path(path)
    if not p.is_file():
        return
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


if __name__ == "__main__":
    load_dotenv()
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")))  # noqa: S104
