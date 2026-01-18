# Tests for job_runner v4.0

These tests are focused on validating the structure and behavior of `v4.0.yaml`.
They act as regression checks for the workflow definition, ensuring the key jobs,
inputs, and job scripts stay consistent as the workflow evolves.

## What is covered

- Workflow structure: required jobs, inputs, and dependencies.
- Job wiring: `if` conditions, outputs, and shared `working-directory`/SSH config.
- Script content: expected directives and control flow in the run/cleanup scripts.
- Input defaults and visibility logic for SSH/SLURM/PBS configuration.

## Running the tests

1) Install test dependencies (preferred: uv):

```bash
uv pip install -r requirements-test.txt
```

If you don't use uv, use pip:

```bash
python3 -m pip install -r requirements-test.txt
```

2) Run the test suite:

```bash
pytest
```

## Notes

- These tests do not execute jobs; they validate the workflow definition itself.
- The checks are intentionally string-based for the shell snippets to catch
  accidental edits in critical control-flow blocks.
