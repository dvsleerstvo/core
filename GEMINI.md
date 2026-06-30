# Project: DV SLEERSTVO (ДВ СЛЕЕРСТВО) - Geometry Dash Demonlist

A specialized leaderboard and record tracking system for Geometry Dash players in the Russian Far East (Primorsky Krai, Khabarovsk Krai, etc.).

## 🏗 Tech Stack

### Backend
- **Framework**: Django 5.2+ (Python 3.13+)
- **API**: Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Caching**: Redis
- **Auth**: Discord OAuth2 (via `django-allauth`)
- **UI Framework (Admin)**: `django-unfold` (modern admin interface)
- **Task Management**: `uv` for python dependency management

### Frontend
- **Framework**: Svelte 5 (with SvelteKit 2)
- **Styling**: Vanilla CSS (modularized in `static/css` and `frontend/static/css`)
- **Mapping**: Leaflet (for regional player distribution)
- **Charts**: Chart.js (for player/level statistics)
- **Language**: TypeScript

## 📂 Project Structure

- `/demonlist`: Core Django app containing models, API views, and business logic.
- `/frontend`: SvelteKit application.
- `/core`: Django project configuration.
- `/discordbot`: Discord bot for record notifications and synchronization.
- `/static`: Legacy/Global static files.
- `/templates`: Custom Django templates (mostly for admin overrides).
- `/maptest`: Experimental map-related functionality.

## 🛠 Core Models & Logic

- **Level**: GD levels with rankings (PC/Mobile), points, and minimum progress requirements.
- **User**: Player profiles linked to GD accounts and Discord. Tracks scores and hardest completions.
- **Victor**: Verified completions or significant progress on levels.
- **RecordRequest**: Submission system for players to verify new records.
- **DiscordLink**: Connection between the site's Django User and the `demonlist.User` profile.

## 📋 General Instructions & Standards

- **Code Style**: 
    - **No comments in code** (write self-documenting code).
    - Follow existing naming conventions (snake_case for Python, camelCase for JS/TS).
    - Use type hints in Python and strict typing in TypeScript.
- **API**:
    - Backend API is prefix-less or under `/api/` (check `core/urls.py`).
    - Frontend communicates with the backend via `frontend/src/lib/api.ts`.

## 🚀 Commands & Development

- **Run Tests**: `docker compose -f docker-compose.test.yml run web uv run manage.py test`
- **Run Locally**: `docker compose up` (starts Django, Postgres, Redis, and SvelteKit).
- **Dependency Management**: Use `uv` for backend and `npm` for frontend.
- **Environment**: Optimized for NixOS with home-manager.

## 🗺 Regional Context
The project focuses on specific Russian regions (Primorye, Khabarovsk, etc.). Region codes and names are defined in `demonlist/variable.py`.


## Site URL
Site hosted in domain "dvsleerstvo.ru".
