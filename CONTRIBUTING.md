# Contributing to EcoPack-AI

Thank you for your interest in contributing.

## Development setup

1. Fork the repository and clone your fork.
2. Create and activate a virtual environment.
3. Install backend dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

4. Create `.env` from `.env.example` and update values.
5. Run the app from `backend/`:

   ```bash
   python app.py
   ```

## Branching

- Use feature branches: `feature/<short-description>`
- Use fix branches: `fix/<short-description>`

## Commit style

- Prefer Conventional Commits:
  - `feat: add analytics export endpoint`
  - `fix: correct recommendation ranking edge case`
  - `docs: update deployment section`

## Pull request checklist

- Keep changes focused and small.
- Update docs if behavior changes.
- Verify endpoints still return expected responses.
- Ensure no secrets are committed.
