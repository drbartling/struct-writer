# Python Template

Template for a stand-alone python tool or script

## About the Template

Replace this section with "About `project name`"

This template sets up a python project using poetry to manage dependencies, pytest for unit testing, pyinstaller for building an executable, and wix for creating a windows installer for distribution.

## Getting Started

### Setup
- Install the latest version of python
	- MacOS: `brew install python`
	- Windows: `winget install Python.Python.3.11`
	- Ubuntu: `sudo apt install python`
- Install [poetry](https://python-poetry.org/)
	- [Installation Instructions](https://python-poetry.org/docs/#installation)
- Install project dependencies:
	- `poetry install`
- Activate project virtual environment:
	- `poetry shell`
- Run the example program
	- `hello Bob`

### Testing

```bash
pytest
```

### Building Executable

```bash
python tools/app_build.py
```

### Building The Windows Installer

- Install build dependencies
	- Windows: `winget install WixToolset.AdditionalTools`
- Build the installer
	- `python tools/installer_build.py`

## Using the Template
Modify the getting started section for your specific application.  Update the rest of the template mostly by searching for "hello" and replacing it with what's appropriate for your application.

		In `tools/installer_build.py`, replace the `uuid.uuid4()` calls with a fixed [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) ([GUID](https://learn.microsoft.com/en-us/dotnet/api/system.guid?view=net-7.0)).

Change this:
```python
f'-dupgrade_code="{uuid.uuid4()}"',  # TODO: Hard code a permanent uuid
f'-dpath_code="{uuid.uuid4()}"',  # TODO: Hard code a permanent uuid
```
Into this:
```python
'-dupgrade_code="12345678-90ab-cdef-1234-567890abcdef"',
'-dpath_code="12345678-90ab-cdef-1234-567890abcdef"',
```

## Template Goal

Most people and organisations have figured out hot to implement the features customers are requesting.  But often "doing things the right way" is deferred until it becomes nearly impossible to ever do things the "right way".

I want to make it easy to start a new project with tests, documentation, installers, etc.  Everything that makes it easier to get those features out the door and delivered relatively stress free.

I don't think this template does that for a oython project, yet, but it puts a few things in place and will make it easier for people I know to start a new python project and deliver it to co-workers, customers, freinds, and family.

Hope it helps.

## Feedback
Create issues or pull requests if you think there's a way to improve it.
