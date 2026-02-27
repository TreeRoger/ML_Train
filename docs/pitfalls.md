# Pitfalls I Hit (and Fixes)

This file tracks real issues encountered while building this project.

## 1) GitHub Actions YAML parsing failures
- Symptom: CI failed with invalid workflow syntax around multiline Python command.
- Root cause: malformed multiline block in `ci.yml`.
- Fix: switched to a one-line `python -c` import smoke test.

## 2) Pydantic v2 `model_config` conflict
- Symptom: backend import crashed with `TypeError: 'FieldInfo' object is not iterable`.
- Root cause: `model_config` is reserved in Pydantic v2 internals.
- Fix: internal field renamed to `architecture_config` with alias `model_config` to keep API stable.

## 3) Dashboard TypeScript shape mismatch
- Symptom: CI dashboard build failed with `Property 'value' does not exist`.
- Root cause: chart code accessed `.value` after mapping to `{loss}` / `{accuracy}` keys.
- Fix: updated chart merge logic to use `.loss` and `.accuracy`.

## 4) CD buildx cache backend error
- Symptom: CD matrix failed with buildx cache backend error.
- Root cause: Buildx not initialized before `docker/build-push-action` with `type=gha` cache.
- Fix: added `docker/setup-buildx-action` to CD workflow.
