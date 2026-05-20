# Project Instructions (for AI agents)

> This file is read by AI agents (Codebuff, etc.) at the start of each conversation.
> Edit it to persist important project rules, preferences, and workflows.

## Railway CLI

For any Railway operations (logs, status, deployments, env vars), **always use the Railway CLI** (`railway` command) instead of the web UI.

## Available services

- **API** — `railway.api.toml` (Dockerfile.api)
- **Mini App** — `railway.miniapp.toml` (Dockerfile, in `miniapp/`)
- **Bot** — `railway.toml` (root, `bot/`)

## Common railway commands

```bash
# View logs
railway logs --service api
railway logs --service miniapp
railway logs --service bot

# Check status
railway status
railway service

# Environment variables
railway variables

# Redeploy
railway up
```