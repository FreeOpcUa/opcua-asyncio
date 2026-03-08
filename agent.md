# Agent Guidelines

## Running

- Use `uv` to run commands: `uv run pytest ...`

## Code Style

- Type annotations are required on all new and modified functions.
- Do not add comments to the code. The code should be self-explanatory. If it is not, refactor it.
- Line length limit is 120 characters.
- Use `ruff` for formatting and linting: `uv run ruff check` and `uv run ruff format`.
- Target Python 3.10+. Use modern syntax (`X | Y` unions, `list[...]`, `dict[...]`, etc.).

## Testing

- Tests use `pytest` with `pytest-asyncio` in auto mode.
- Run specific tests with: `uv run pytest tests/<file>.py -k "<pattern>" -x`
