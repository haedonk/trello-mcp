# Setup

## 1) Trello credentials

You need:
- Trello API key
- Trello token
- A board ID you can access

If you don’t have these yet, see: `trello-api-key.md`.

Set these environment variables:
- `TRELLO_API_KEY`
- `TRELLO_TOKEN`
- `TRELLO_BOARD_ID` (optional)

If you don’t set `TRELLO_BOARD_ID`, you can call `get_boards()` and then `set_board(board_id)` after connecting.

This repo includes `.env.example`, but `server.py` does **not** automatically load a `.env` file.

## 2) Install

```bash
python -m venv .venv
# activate the venv for your shell
pip install -r requirements.txt
```

## 3) Run (SSE recommended)

SSE is the most common transport for MCP client/server setups.

```bash
export MCP_TRANSPORT=sse
export MCP_PORT=8000
python server.py
```

You should then have an SSE endpoint at:

- `http://localhost:8000/sse`

## 4) Configure your MCP client

You must:
1) **Run the server** (SSE recommended), then
2) Configure your MCP client to point at the server’s SSE URL.

### Claude Code

Claude Code can be configured either:
- **Globally** (one MCP config for all projects), or
- **Per-project** by placing a `.mcp.json` file in the directory you’re working in.

This repo includes a `.mcp.json` template already set to:

- `http://localhost:8000/sse`

If you run the server on another host/port, update the URL accordingly.
