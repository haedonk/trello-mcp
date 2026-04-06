# Tools

`trello-mcp` exposes Trello actions as MCP tools (see `server.py`). Payloads are derived from the function signatures and Pydantic models.

## Board

### `get_boards()`
Returns boards accessible to the authenticated user.

### `set_board(board_id: str)`
Sets the active board for subsequent requests.

## Lists

### `get_lists()`
Lists lists on the active board.

### `create_list(name: str)`
Creates a list.

## Cards

### `create_cards(cards: list[{list_id, name, desc?, label_ids?, member_ids?}])`
Example:

```json
{
  "cards": [
    {"list_id": "<listId>", "name": "Task A", "desc": "Optional description"}
  ]
}
```

### `update_cards(updates: list[{card_id, name?, desc?, list_id?}])`
Example:

```json
{
  "updates": [
    {"card_id": "<cardId>", "name": "New title"}
  ]
}
```

## Checklists

### `create_checklists(checklists: list[{card_id, name}])`
Example:

```json
{
  "checklists": [
    {"card_id": "<cardId>", "name": "Definition of Done"}
  ]
}
```

### `add_checklist_items(items: list[{checklist_id, name}])`
Example:

```json
{
  "items": [
    {"checklist_id": "<checklistId>", "name": "Write unit tests"}
  ]
}
```

### `update_checklists(updates: list[{checklist_id, name?, card_id?}])`
- Rename: set `name`
- Move to another card: set `card_id` (sent to Trello as `idCard`)

Example (rename):

```json
{
  "updates": [
    {"checklist_id": "<checklistId>", "name": "DoD"}
  ]
}
```

Example (move):

```json
{
  "updates": [
    {"checklist_id": "<checklistId>", "card_id": "<newCardId>"}
  ]
}
```

### `delete_checklists(deletes: list[{checklist_id}])`
Example:

```json
{
  "deletes": [
    {"checklist_id": "<checklistId>"}
  ]
}
```

## Notes

- IDs like `<cardId>`/`<listId>`/`<checklistId>` are Trello IDs.
- The AI/tooling can typically see the required payload shape via the MCP tool schema (if the MCP client supports schemas).

