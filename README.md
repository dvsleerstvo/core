# DV SLEERSTVO (ДВ СЛЕЕРСТВО) - Geometry Dash Demonlist

[English](README.md) | [Русский](README.ru.md)
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
- **Styling**: Vanilla CSS
- **Mapping**: Leaflet (for regional player distribution)
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

## 🚀 Running Locally

The project is fully dockerized for ease of development.

1. Clone the repository:
   ```bash
   git clone https://github.com/dvsleerstvo/core.git
   cd core
   ```

2. Create a `.env` file from the example (if available) or set the required environment variables:
   - `SECRET_KEY`
   - Discord bot credentials (`BOT_TOKEN`, `BOT_API_SECRET`, `REQUEST_CHANNEL_ID`)
   - S3 configuration for backups (optional)

3. Start the application using Docker Compose:
   ```bash
   docker compose up --build
   ```
   *Note: By default, the Discord bot container will **not** start. If you want to run the bot alongside the project, use the `bot` profile:*
   ```bash
   docker compose --profile bot up --build
   ```

## 🧪 Testing

To run backend tests:
```bash
docker compose -f docker-compose.test.yml run web uv run manage.py test
```

## 🤝 Contributing

Contributions are welcome! Please make sure to read the [CONTRIBUTING.md](CONTRIBUTING.md) (if provided) and follow the code style guidelines:
- Python: PEP 8, formatted with `ruff` / `black` (or similar standard).
- TypeScript/Svelte: Prettier and strict TypeScript typings.
- Use self-documenting code rather than excessive comments.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
