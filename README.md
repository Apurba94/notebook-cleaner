# notebook-cleaner

**Commit Jupyter notebooks without the noise: strip outputs, execution counts and volatile
metadata, check cleanliness in CI or pre-commit, and catch API keys before they are published.**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Notebooks with outputs make huge, unreadable diffs, leak data (patient rows printed in a cell,
local paths) and credentials, and bloat repositories with images. Execution counts change on every
run, creating merge conflicts. Clean notebooks are small, reviewable and must be re-run to see
results, which is itself a reproducibility check.

## Features

- Removes outputs (or only outputs above `--max-output-kb`), resets execution counts
- Drops noisy cell metadata (`ExecuteTime`, `collapsed`, `scrolled`, ...) but keeps `tags`
  (needed by papermill parameters) unless `--drop-tags`
- Reduces notebook metadata to `kernelspec` and `language_info` (removes widget state, signatures)
- `--check` mode for CI and pre-commit hooks (exit 1 if a notebook needs cleaning)
- `--secrets` scans sources and outputs for AWS/GitHub/Slack tokens, private keys and `api_key = "..."`
- `--stats`: size of outputs, out-of-order execution, empty cells

## Usage

```bash
pip install .
notebook-cleaner analysis/*.ipynb
notebook-cleaner --check notebooks/*.ipynb          # in CI
notebook-cleaner --secrets --stats report.ipynb
```

Pre-commit hook (`.pre-commit-config.yaml`):

```yaml
- repo: local
  hooks:
    - id: notebook-cleaner
      name: notebook-cleaner
      entry: notebook-cleaner --check
      language: system
      files: \.ipynb$
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
