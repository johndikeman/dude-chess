# Dude Chess Agent

A specialized version of `dude-agent` focused on maintaining a humorous Lichess Blunder Blog.

## Features

- Daily Lichess check for new games via systemd timer.
- Automated blog post generation (1000+ words, humorous, informal, profanity-heavy).
- Automatic screenshot capture for key positions.
- Integrated with the `dude-agent` core for self-improvement.

## Tech Stack
- **dude-agent**: The underlying self-improving agent framework.
- **Nix Flakes**: For dependency management and service configuration.
- **Discord.js**: For communication and task management.
- **Lichess API**: For fetching recent games.
- **GitHub CLI (gh)**: For PR management.

## Setup
1. Clone this repository to `/home/ubuntu/dude-workspace/dude-chess`.
2. Ensure Nix is installed with Flakes enabled.
3. Configure your `.env` file in `~/.config/dude-chess/.env` with:
   - `DISCORD_TOKEN`
   - `GEMINI_JSON_TOKEN`
   - `GITHUB_REPO=johndikeman/dude-chess`
4. Use the provided Nix home-manager module to enable the `dude-chess` service.

## Configuration
The agent uses a separate config directory from the main `dude` agent:
`DUDE_CONFIG_DIR=/home/ubuntu/.config/dude-chess`

This directory contains:
- `tasks.md`: The task queue for the chess agent.
- `config.json`: Agent configuration (model, auto-next, etc.).
- `agent.log`: Activity log.
- `sessions/`: History of agent sessions.
- `lichess-tracking.json`: Keeps track of the last analyzed game.

## Services
- `dude-chess.service`: The main agent process.
- `lichess-check.service` & `lichess-check.timer`: Periodically checks for new games and adds tasks to `tasks.md`.

