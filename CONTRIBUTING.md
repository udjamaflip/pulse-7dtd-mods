# Contributing

Contributions are welcome. Please follow these guidelines.

## Bug Reports

Open a GitHub Issue and include:
- Your game version (A21 / V1.x / Experimental)
- The mod type you were generating
- Steps to reproduce
- Any error messages from the browser or server logs

## Feature Requests

Open a GitHub Issue with the prefix `[feature]` in the title. Describe the use case and what mod content it would support.

## Pull Requests

1. Fork the repo and create a branch from `main`
2. Keep each PR focused on a single feature or fix
3. Add or update tests in `tests/` for any logic changes
4. Confirm all tests pass: `pytest`
5. Do not introduce new external dependencies without discussion
6. Open the PR against `main` with a clear description of the change

## Code Style

- Plain Python 3.11+, no complex frameworks
- No external dependencies beyond what is listed in `requirements.txt`
- Use stdlib `xml.etree.ElementTree` for all XML generation
- Keep functions small and testable
- No hardcoded paths, usernames, or system-specific values in source

## Questions

Open an Issue with the `[question]` prefix.
