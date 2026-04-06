# Using this project with Claude Code

This repo is designed to work well with Claude Code via MCP.

## 1) Run the server (SSE recommended)

```bash
export MCP_TRANSPORT=sse
export MCP_PORT=8000
python server.py
```

SSE endpoint:

- `http://localhost:8000/sse`

## 2) Configure Claude Code to connect to the server

You can configure MCP in Claude Code either:

- **Globally** (applies to all projects), or
- **Per-project** by placing a `.mcp.json` file in the directory you’re working in

This repo ships with a `.mcp.json` template that points to:

- `http://localhost:8000/sse`

## 3) How Claude should decide payloads

Claude can typically see each tool’s **payload schema** through MCP (tool name, description, required arguments, and types). If you ever want to double-check required fields, ask Claude to call `tools/list`.

## 4) File-driven workflow (recommended)

If you have a lot of cards/checklists to create or update, it’s often easiest to provide Claude a file describing what you want.

You **don’t have to use JSON**, but structured input helps:

- **JSON**: lowest token usage, least ambiguity, easiest for Claude to map into tool payloads.
- **Markdown (tickets)**: more flexible to write, but Claude will spend more tokens parsing/normalizing it.

### Option A: JSON input (lowest token usage)

Create a JSON file like `cards-to-create.json`:

```json
[
  {
    "list_name": "To Do",
    "name": "Draft project outline",
    "desc": "First pass outline"
  },
  {
    "list_name": "In Progress",
    "name": "Implement checklist tools",
    "desc": "Add update/delete"
  }
]
```

Or `cards-to-update.json`:

```json
[
  {
    "card_id": "<cardId>",
    "name": "Updated title"
  },
  {
    "card_id": "<cardId>",
    "desc": "Updated description"
  }
]
```

### Option B: Markdown ticket file (easiest to author)

Create a Markdown file like `tickets.md`:

```md
# Trello updates

## Create
- List: To Do
  Title: Draft project outline
  Description: First pass outline

## Update
- Card ID: <cardId>
  Title: Updated title

## Move
- Card ID: <cardId>
  Move to list: In Progress
```

Claude can read this and then translate it into calls like `create_cards`, `update_cards`, and `move_cards`.

### What Claude does with the file

Typical pattern:

1. Claude reads your file.
2. Claude gathers any missing IDs:
   - calls `get_lists()` to map list names to list IDs
   - calls `get_cards()` / `search_cards()` if it needs to look up cards
3. Claude calls the right batch tools:
   - `create_cards` for creates
   - `update_cards` / `move_cards` for updates
   - checklist tools (`create_checklists`, `add_checklist_items`, `update_checklists`, `delete_checklists`) as needed
4. Claude validates results by re-fetching cards/lists.

### What you should include in the file

You *don’t have to include IDs* — Claude can retrieve them from the server (for example via `get_boards`, `get_lists`, `get_cards`, and `search_cards`).

However, providing IDs usually means:
- fewer lookup calls,
- fewer tokens,
- less ambiguity.

To make it reliable, include either:
- explicit IDs (`card_id`, `list_id`, `checklist_id`), OR
- stable names + enough context (e.g., `list_name` + exact card name)

## 5) Planning mode (recommended)

If you’re making real changes to a Trello board, it’s a good idea to have Claude **plan first** and only execute after you approve.

Suggested prompt pattern:

- Ask Claude to **summarize what it understood** from your file/request.
- Ask Claude to **produce a step-by-step plan** (including which tools it will call and what it expects to change).
- Approve the plan.
- Then ask Claude to execute.

This reduces mistakes, especially for batch updates and deletes.

## 6) Safety tips

- If you’re doing destructive operations, ask Claude to do a “dry run” plan first (list what it will change, then execute).
- Use `search_cards` and `get_cards_on_list` to confirm Claude is operating on the intended items.
