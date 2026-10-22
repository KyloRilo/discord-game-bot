# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Discord bot that manages game server lifecycles (spin up/down) on AWS. The bot runs as an AWS Lambda behind a Discord webhook, and game servers run as ECS tasks from Docker images pushed to ECR.

Key constraint: only one game server can be active at a time.

## Architecture

- **`bot.py`** — Discord bot entry point using discord.py with `!` command prefix. Currently a skeleton; intended to become the Lambda handler that manages ECS game servers.
- **`build/<game>/`** — Each subdirectory contains a Dockerfile and startup script for a game server image. Servers are installed via SteamCMD.
- **AWS integration** — Servers use Secrets Manager for login tokens, EventBridge for activity-check crons, and ECS for hosting. On spin-up: generate token, create cron, start backups. On spin-down: final backup, disable cron, erase token.

## Game Servers

| Game | Directory | Ports | Status |
|------|-----------|-------|--------|
| Valheim | `build/valheim/` | 2456-2458/udp | Active |
| Windrose | `build/windrose/` | 7777/udp+tcp | Not yet enabled |
| Minecraft | — | — | Future |

## Commands

```bash
# Install bot dependencies
pip install -r requirements.txt

# Build game server images
docker build -t valheim-server build/valheim/
docker build -t windrose-server build/windrose/

# Run game servers locally
docker run -d --name valheim -p 2456-2458:2456-2458/udp -e SERVER_NAME="Valhalla" -e WORLD_NAME="Midgard" -e SERVER_PASS="supersecret" valheim-server
docker run -d --name windrose -p 7777:7777/udp -p 7777:7777/tcp windrose-server
```

## Dev Environment

A VS Code devcontainer is configured (Python 3.11). Dependencies are auto-installed via `postCreateCommand`.
