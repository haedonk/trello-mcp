# Using this project with Postman

There are two common ways to use Postman with this repo:

1. **Talk to the MCP server** (recommended if you want to test the MCP protocol)
2. **Talk to Trello’s REST API directly** (useful for validating raw Trello responses)

This repo includes two Postman collections:

- `Trello_MCP_Server.postman_collection.json` — calls the MCP server over SSE + JSON-RPC
- `Trello_API_AI_Stem_Board.postman_collection.json` — calls Trello’s REST API directly

## Prerequisite: run the server (for the MCP collection)

Run the server with SSE (recommended for MCP):

```bash
export MCP_TRANSPORT=sse
export MCP_PORT=8000
python server.py
```

Your SSE endpoint should be:

- `http://localhost:8000/sse`

## Option A: Use Postman manually (hands-on)

### A1) MCP Server collection (SSE + JSON-RPC)

The MCP server requires a short handshake before you can call any tools:

1) **Connect to SSE** (`GET /sse`) to start the stream.
2) The server sends an `event: endpoint` message containing a **session-specific messages URL** like:

- `/messages/?session_id=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX`

3) **Initialize** the session by sending the JSON-RPC `initialize` request to that session URL.
4) After initialization, you can call `tools/list` and `tools/call`.

In Postman, that maps directly to the first requests in the collection:

1. Import `Trello_MCP_Server.postman_collection.json` into Postman.
2. Set the collection variable `base_url` (default is `http://localhost:8000`).
3. Run **`1. Connect (SSE)`**.
   - In the response stream, find the line starting with `data:`.
   - It looks like: `/messages/?session_id=...`
   - Copy the UUID portion into the collection variable `session_id`.
4. Run **`2. Initialize`**.
   - This is required before tool calls will work.
5. (Optional) Run **`3. List Tools`** to confirm tool schemas.
6. Run tool calls under folders like **Board**, **Cards**, **Checklists**, etc.

**Common gotchas**

- If you skip **`2. Initialize`**, tool calls won’t work because the MCP session wasn’t established.
- If you don’t copy the `session_id` from the SSE `data:` line, you’ll end up POSTing to the wrong `/messages` endpoint.

### A2) Trello API collection

1. Import `Trello_API_AI_Stem_Board.postman_collection.json`.
2. Fill in collection variables:
   - `api_key`
   - `token`
   - `board_id` (optional, but many requests use it)
3. Run requests to create/update cards, checklists, etc.

## Option B: “Collect data then have an AI string it together”

This workflow is useful when you have a lot of changes to make and don’t want to click through Postman repeatedly.

### B1) Collect the IDs you need

Using Postman (or any method), collect:
- `board_id` (optional if you will call `set_board`)
- `list_id`
- `card_id`
- `checklist_id`

### B2) Ask an AI to build a runbook

Give the AI:
- your desired outcome (e.g., “rename these 20 cards”, “move these cards”, “add checklist items”)
- the IDs you gathered
- the required payload shapes (or simply point it at `tools/list` output)

Ask it to output either:
- a sequence of Postman-ready requests, or
- a command-line script (for example using `curl`) that makes the same calls in order.

### B3) Run and verify

Execute the runbook and verify results:
- For MCP: use `get_cards`, `search_cards`, etc.
- For raw Trello API: re-run the relevant GET endpoints

## Tips

- The MCP server advertises **tool schemas**. In Postman, **`tools/list`** is the fastest way to see the expected input payload.
- If you’re doing many operations, prefer *batch tools* (e.g. `create_cards`, `update_cards`) over one-at-a-time calls.
