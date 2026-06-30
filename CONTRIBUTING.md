# Contributing to DV SLEERSTVO (ДВ СЛЕЕРСТВО)

First off, thank you for considering contributing to the DV SLEERSTVO (ДВ СЛЕЕРСТВО) - Geometry Dash Demonlist! It's people like you that make open source projects great.

## Code of Conduct

By participating in this project, you are expected to uphold general open source etiquette: be respectful and collaborative.

## Development Setup

1. **Prerequisites:**
   - Docker and Docker Compose
   - Node.js (for frontend standalone development, though Docker handles it)
   - Python 3.13+ (for backend standalone development)
   - `uv` for python dependencies.

2. **Running the project:**
   See the `README.md` for instructions on how to start the local environment via Docker Compose.

3. **Running Tests:**
   Please ensure tests pass before submitting a Pull Request:
   ```bash
   docker compose -f docker-compose.test.yml run web uv run manage.py test
   ```

## Code Style & Conventions

- **General:**
  - Write self-documenting code. Avoid redundant comments in code; instead, use clear variable, function, and class names.
  
- **Backend (Python/Django):**
  - Use `snake_case` for variables and functions.
  - Use Type Hints wherever possible.
  - Follow PEP 8 guidelines.

- **Frontend (Svelte/TypeScript):**
  - Use `camelCase` for variables and functions.
  - Use strict typing in TypeScript.

## How to Contribute

1. Fork the repository.
2. Create a new branch for your feature or bugfix (`git checkout -b feature/your-feature-name`).
3. Make your changes and test them thoroughly.
4. Commit your changes. (If you're using our tools, you can use semantic commit messages).
5. Push to the branch (`git push origin feature/your-feature-name`).
6. Create a Pull Request against the main branch.

Please provide a clear description of the problem you're solving and the solution you've implemented in your Pull Request.
