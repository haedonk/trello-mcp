# trello-mcp

A small MCP server that exposes common Trello operations (boards, lists, cards, labels, checklists) as MCP tools.

## What you get

- Board tools: list boards, set active board, board info/members/labels
- List tools: list/create lists
- Card tools: list/search/create/update/move/delete cards
- Checklist tools: create checklists, add checklist items, **update checklists**, **delete checklists**

## Requirements

- Python 3.12+ (Docker option also available)
- A Trello API key + token

## Environment variables

Copy `.env.example` to `.env` and fill values:

- `TRELLO_API_KEY` – Trello API key
- `TRELLO_TOKEN` – Trello token
- `TRELLO_BOARD_ID` – (optional) default board used when you haven't called `set_board`
- `MCP_TRANSPORT` – one of `sse` (recommended), `http`, or `stdio`
- `MCP_PORT` – (optional) port for `http`/`sse` transports (default: `8000`)

### Checking env vars

#### macOS / Linux (bash, zsh)

```bash
# Print a single value
echo "$TRELLO_API_KEY"

# List all Trello-related vars
env | grep '^TRELLO'

# Check whether it's set
[ -n "$TRELLO_API_KEY" ] && echo "set" || echo "not set"
```

#### Windows (PowerShell)

```powershell
# Print a single value
$env:TRELLO_API_KEY

# List all Trello-related vars
Get-ChildItem Env: | Where-Object Name -like "TRELLO*"

# Check whether it's set
Test-Path env:TRELLO_API_KEY
```

> Note: this project does not automatically load a `.env` file. Either set env vars in your shell,
> or use a tool like `python-dotenv` (not included) / your IDE or container runtime configuration.

## Install

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

### Recommended: SSE (best for MCP client/server setup)

macOS / Linux:

```bash
export MCP_TRANSPORT=sse
export MCP_PORT=8000
python server.py
```

Windows (PowerShell):

```powershell
$env:MCP_TRANSPORT = "sse"
$env:MCP_PORT = "8000"
python server.py
```

### Alternative: stdio

macOS / Linux:

```bash
export MCP_TRANSPORT=stdio
python server.py
```

Windows (PowerShell):

```powershell
$env:MCP_TRANSPORT = "stdio"
python server.py
```

### Alternative: HTTP (streamable)

macOS / Linux:

```bash
export MCP_TRANSPORT=http
export MCP_PORT=8000
python server.py
```

Windows (PowerShell):

```powershell
$env:MCP_TRANSPORT = "http"
$env:MCP_PORT = "8000"
python server.py
```

## Docker

```bash
docker build -t trello-mcp .

# SSE recommended
docker run --rm -p 8000:8000 \
  -e TRELLO_API_KEY=... \
  -e TRELLO_TOKEN=... \
  -e TRELLO_BOARD_ID=... \
  -e MCP_TRANSPORT=sse \
  -e MCP_PORT=8000 \
  trello-mcp
```

> `TRELLO_BOARD_ID` is optional if you plan to call `get_boards` and `set_board` during your session.

## Tool notes / examples

This server implements tools in `server.py` using `@mcp.tool()`.

### Checklists

- `create_checklists([{card_id, name}, ...])`
- `add_checklist_items([{checklist_id, name}, ...])`
- `update_checklists([{checklist_id, name?, card_id?}, ...])`
  - rename: provide `name`
  - move to another card: provide `card_id`
- `delete_checklists([{checklist_id}, ...])`

## Troubleshooting

- **KeyError: 'TRELLO_API_KEY'** (or token/board): the environment variable isn’t set for the running process.
- **401/invalid token**: regenerate your Trello token and confirm it matches the API key.
- **Board not found**: confirm `TRELLO_BOARD_ID` is a board you can access (or call `set_board`).

## Using with Claude Code (MCP)

1) **Run this server first** (SSE recommended). By default the SSE endpoint is:

- `http://localhost:8000/sse`

2) **Tell Claude Code where to find the server**.

Claude Code can be configured either:
- **Globally** (applies to all your projects), or
- **Per-project** by putting a `.mcp.json` in the directory you’re working in.

This repo includes a template `.mcp.json` already configured for local SSE.

> Exact menu/paths can vary by Claude Code version. The key idea is that Claude Code needs an MCP server entry that matches the `type` (SSE) and `url`.

## Tool payloads (can the AI see required fields?)

Usually, yes.

MCP tools are advertised to clients along with an **input schema** (often JSON Schema) derived from the tool’s function signature and Pydantic models. If your MCP client supports tool schemas, the AI can see the required payload shape (field names, types, which are required) before it calls the tool.

What the schema *doesn’t* provide is valid Trello IDs—you still need to obtain IDs via tools like `get_boards`, `get_lists`, `get_cards`, etc.
