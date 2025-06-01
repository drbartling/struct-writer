set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

default:
    just --list

# install the uv package manager
[linux]
[macos]
install_uv:
    curl -LsSf https://astral.sh/uv/install.sh | sh

# install the uv package manager
[windows]
install_uv:
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

test:
    uv run pytest

lint:
    uv run ruff check

setup:
    uv venv --python 3.13.0
    uv sync
