# Workflow

## Branches
- `main` is protected: changes go through pull requests, CI must pass.
- Branch names: `feat/<thing>`, `fix/<thing>`, `docs/<thing>`, `hw/<thing>`, `ml/<thing>`.

## Commits (Conventional Commits)
- `feat: add UART ring buffer`
- `fix: correct DMA half-transfer flag clear`
- `docs: add power budget`
- `test: add kurtosis edge cases`
- `chore: bump ruff`

## Releases
Semantic versioning tags: `v0.1.0`, `v0.2.0`, ...

## Local setup
Option A — Dev Container (recommended): open the repo in VS Code → "Reopen in Container".

Option B — Docker CLI:
```bash
docker build -t motorsense-dev .
docker run --rm -it -v "$PWD":/workspace motorsense-dev bash
```

Then once: `pre-commit install`.

## Embedded rules (firmware/)
- Build with `-Wall -Wextra -Werror`.
- No dynamic allocation after init.
- Layers: drivers → services → app. App code never touches registers.
- Fixed-width types (`uint32_t`), `static_assert` on assumptions.
- Every driver has host-side unit tests with mocks where possible.
