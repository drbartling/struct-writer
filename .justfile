set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

default:
    @just --list

# install the uv package manager
[linux]
[macos]
install_uv:
    @curl -LsSf https://astral.sh/uv/install.sh | sh

# install the uv package manager
[windows]
install_uv:
    @powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

test: check
    @uv run pytest

check: format
    @uv run ruff check --exit-zero

fix: format
    @uv run ruff check --fix

format:
    @uv run ruff format

loop:
    @watchexec \
        --clear=reset \
        --restart  \
        --debounce 500 \
        --exts py,yml,toml,ini,bin \
        just test

setup:
    @uv venv --python 3.13.0
    @uv sync
