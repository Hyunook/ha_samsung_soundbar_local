# 🤝 Contributing

Thanks for helping improve Samsung Soundbar (Local)!

## 🔒 No personal data

This repository may only contain synthetic data. Never commit:

- real IP or MAC addresses, serial numbers, device or Home Assistant IDs
- tokens, passwords, cookies or keys
- logs, diagnostics, network captures, screenshots or Home Assistant configuration

Tests use placeholders such as `example.invalid` and generated MAC addresses.
Run the privacy check before every commit:

```sh
python scripts/check_privacy.py
```

To run it automatically, enable the pre-commit hook in a local `.githooks/`
folder and run `git config core.hooksPath .githooks`. CI runs the same check
on every push and pull request.

## 🧪 Tests

The tests run inside the official Home Assistant container. You only need Docker:

```sh
docker run --rm -v "$PWD:/workspace" -w /workspace -e PYTHONPATH=/workspace \
  --entrypoint python ghcr.io/home-assistant/home-assistant:stable \
  tests/test_integration.py
```

Lint and format with [Ruff](https://docs.astral.sh/ruff/):

```sh
ruff check . && ruff format --check .
```

## 🔄 CI

| Workflow | Checks |
| --- | --- |
| `Validate` | HACS action and hassfest (push, pull request, daily) |
| `Tests` | Ruff, privacy check and integration tests on the minimum and latest Home Assistant version |

Dependabot keeps the GitHub Actions up to date.

## 🚀 Releases

1. Update `version` in `manifest.json` and add an entry to `CHANGELOG.md`.
2. Make sure all workflows are green.
3. Create a GitHub release with the tag `vX.Y.Z`.
