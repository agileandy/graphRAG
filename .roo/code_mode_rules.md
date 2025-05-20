# Code Mode Rules

## Python Projects

When working on Python projects, please adhere to the guidelines outlined in the [Python Project Guidelines](./python_guidelines.md). This includes, but is not limited to:
- Using `uv` for package management.
- Running Python scripts with `uv run <filename.py>`.

When starting to work on a new task or feature, create a git branch to manage the changes.
- Everytime a piece of code is built and it passes it's test then complete the following.
    - perform uv ruff to lint the code
    - commit the changes
- if the tests indicate that the feature is then complete, merge into the parent branch (or main if on a direct branch)
-