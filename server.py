import asyncio
import json
import logging
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("trello-mcp")

mcp = FastMCP("Trello", host="0.0.0.0")


BASE_URL = "https://api.trello.com/1"


def _auth_params() -> dict[str, str]:
    return {
        "key": os.environ["TRELLO_API_KEY"],
        "token": os.environ["TRELLO_TOKEN"],
    }


_active_board_id: str | None = None


def _board_id() -> str:
    return _active_board_id or os.environ["TRELLO_BOARD_ID"]


async def _request(method: str, path: str, params: dict | None = None) -> str:
    log.debug("%s %s", method, path)
    all_params = _auth_params()
    if params:
        all_params.update(params)
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, f"{BASE_URL}{path}", params=all_params)
        log.debug("%s %s -> %d", method, path, resp.status_code)
        resp.raise_for_status()
        return json.dumps(resp.json(), indent=2)


async def _request_json(method: str, path: str, params: dict | None = None) -> Any:
    log.debug("%s %s", method, path)
    all_params = _auth_params()
    if params:
        all_params.update(params)
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, f"{BASE_URL}{path}", params=all_params)
        log.debug("%s %s -> %d", method, path, resp.status_code)
        resp.raise_for_status()
        return resp.json()


_CARD_FIELDS = {"id", "name", "desc", "idList", "idBoard", "idLabels", "idMembers", "due", "dueComplete", "closed", "pos", "shortUrl"}


def _strip_card(card: dict) -> dict:
    return {k: v for k, v in card.items() if k in _CARD_FIELDS}


async def _get_archive_list_id() -> str | None:
    lists = await _request_json("GET", f"/boards/{_board_id()}/lists")
    for lst in lists:
        if lst.get("name") == "Archive":
            return lst["id"]
    return None


# ── Input models ─────────────────────────────────────────────────────────────


class CardInput(BaseModel):
    list_id: str
    name: str
    desc: str = ""
    label_ids: str = ""
    member_ids: str = ""


class CardUpdate(BaseModel):
    card_id: str
    name: str = ""
    desc: str = ""
    list_id: str = ""


class CardMove(BaseModel):
    card_id: str
    list_id: str


class CardLabels(BaseModel):
    card_id: str
    label_ids: list[str]


class CardComment(BaseModel):
    card_id: str
    text: str


class ChecklistInput(BaseModel):
    card_id: str
    name: str


class ChecklistItemInput(BaseModel):
    checklist_id: str
    name: str


class ChecklistUpdate(BaseModel):
    checklist_id: str
    name: str = ""
    card_id: str = ""


class ChecklistDelete(BaseModel):
    checklist_id: str


# ── Board ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_boards() -> str:
    """Get all boards accessible to the authenticated user. Returns [{id, name, url}]."""
    log.info("get_boards")
    data = await _request_json("GET", "/members/me/boards", {"fields": "id,name,url"})
    return json.dumps(data, indent=2)


@mcp.tool()
async def set_board(board_id: str) -> str:
    """Set the active board. All subsequent commands will operate on this board.

    Args:
        board_id: The ID of the board to switch to. Use get_boards to find board IDs.
    """
    global _active_board_id
    log.info("set_board board_id=%s", board_id)
    _active_board_id = board_id
    data = await _request_json("GET", f"/boards/{board_id}", {"fields": "id,name,url"})
    return json.dumps({"ok": True, "active_board": data}, indent=2)


@mcp.tool()
async def get_board_info() -> str:
    """Get full details about the Trello board."""
    log.info("get_board_info")
    return await _request("GET", f"/boards/{_board_id()}")


@mcp.tool()
async def get_board_members() -> str:
    """Get all members on the board."""
    log.info("get_board_members")
    return await _request("GET", f"/boards/{_board_id()}/members")


@mcp.tool()
async def get_board_labels() -> str:
    """Get all labels on the board. Returns [{id, name, color}]."""
    log.info("get_board_labels")
    return await _request("GET", f"/boards/{_board_id()}/labels")


@mcp.tool()
async def create_label(name: str, color: str) -> str:
    """Create a new label on the board.

    Args:
        name: Display name for the label.
        color: Label color. Valid values: black, blue, green, lime, orange, pink,
               purple, red, sky, yellow, null (for no color).
    """
    log.info("create_label name=%r color=%r", name, color)
    return await _request(
        "POST",
        "/labels",
        {"name": name, "color": color, "idBoard": _board_id()},
    )


@mcp.tool()
async def add_labels_to_cards(cards: list[CardLabels]) -> str:
    """Add labels to one or more cards.

    Args:
        cards: List of card-label assignments. Each requires card_id and a list of label_ids.
    """
    log.info("add_labels_to_cards count=%d", len(cards))

    async def _add_label(card_id: str, label_id: str):
        try:
            result = await _request_json("POST", f"/cards/{card_id}/idLabels", {"value": label_id})
            return {"ok": True, "card_id": card_id, "label_id": label_id}
        except Exception as e:
            log.error("add_labels_to_cards: failed card=%s label=%s: %s", card_id, label_id, e)
            return {"ok": False, "card_id": card_id, "label_id": label_id, "error": str(e)}

    tasks = [_add_label(c.card_id, lid) for c in cards for lid in c.label_ids]
    results = await asyncio.gather(*tasks)
    return json.dumps(list(results), indent=2)


# ── Lists ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_lists() -> str:
    """Get all lists (columns) on the board, e.g. To Do, In Progress, Done."""
    log.info("get_lists")
    return await _request("GET", f"/boards/{_board_id()}/lists")


@mcp.tool()
async def create_list(name: str) -> str:
    """Create a new list on the board.

    Args:
        name: Name of the new list.
    """
    log.info("create_list name=%r", name)
    return await _request("POST", "/lists", {"name": name, "idBoard": _board_id()})


# ── Cards ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_cards() -> str:
    """Get all cards across all lists on the board, excluding the Archive list."""
    log.info("get_cards")
    cards, archive_id = await asyncio.gather(
        _request_json("GET", f"/boards/{_board_id()}/cards", {"filter": "open"}),
        _get_archive_list_id(),
    )
    if archive_id:
        before = len(cards)
        cards = [c for c in cards if c.get("idList") != archive_id]
        log.debug("get_cards: filtered %d archive cards, returning %d", before - len(cards), len(cards))
    else:
        log.debug("get_cards: returning %d cards (no Archive list found)", len(cards))
    return json.dumps([_strip_card(c) for c in cards], indent=2)


@mcp.tool()
async def get_cards_on_list(list_ids: list[str]) -> str:
    """Get all cards on one or more lists, excluding the Archive list.

    Args:
        list_ids: List of list IDs. Use get_lists to find list IDs.
    """
    log.info("get_cards_on_list list_ids=%s", list_ids)
    archive_id = await _get_archive_list_id()
    filtered_ids = [lid for lid in list_ids if lid != archive_id]
    if len(filtered_ids) < len(list_ids):
        log.debug("get_cards_on_list: skipped Archive list %s", archive_id)

    async def _get(list_id: str):
        try:
            result = await _request_json("GET", f"/lists/{list_id}/cards", {"filter": "open"})
            log.debug("get_cards_on_list: list %s returned %d cards", list_id, len(result))
            return {"ok": True, "list_id": list_id, "result": [_strip_card(c) for c in result]}
        except Exception as e:
            log.error("get_cards_on_list: list %s failed: %s", list_id, e)
            return {"ok": False, "list_id": list_id, "error": str(e)}

    results = await asyncio.gather(*[_get(lid) for lid in filtered_ids])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def create_cards(cards: list[CardInput]) -> str:
    """Create one or more new cards on specified lists.

    Args:
        cards: List of cards to create. Each card requires list_id and name;
               desc, label_ids (comma-separated), and member_ids (comma-separated) are optional.
    """
    log.info("create_cards count=%d", len(cards))

    async def _create(card: CardInput):
        try:
            params: dict[str, str] = {"idList": card.list_id, "name": card.name}
            if card.desc:
                params["desc"] = card.desc
            if card.label_ids:
                params["idLabels"] = card.label_ids
            if card.member_ids:
                params["idMembers"] = card.member_ids
            result = await _request_json("POST", "/cards", params)
            log.debug("create_cards: created card %r id=%s", card.name, result.get("id"))
            return {"ok": True, "name": card.name, "result": _strip_card(result)}
        except Exception as e:
            log.error("create_cards: failed to create card %r: %s", card.name, e)
            return {"ok": False, "name": card.name, "error": str(e)}

    results = await asyncio.gather(*[_create(c) for c in cards])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def update_cards(updates: list[CardUpdate]) -> str:
    """Update one or more cards' name, description, or list.

    Args:
        updates: List of updates. Each update requires card_id; name, desc, and
                 list_id are optional (omit to keep current value).
    """
    log.info("update_cards count=%d", len(updates))

    async def _update(u: CardUpdate):
        try:
            params: dict[str, str] = {}
            if u.name:
                params["name"] = u.name
            if u.desc:
                params["desc"] = u.desc
            if u.list_id:
                params["idList"] = u.list_id
            result = await _request_json("PUT", f"/cards/{u.card_id}", params)
            log.debug("update_cards: updated card %s fields=%s", u.card_id, list(params.keys()))
            return {"ok": True, "card_id": u.card_id, "result": _strip_card(result)}
        except Exception as e:
            log.error("update_cards: failed to update card %s: %s", u.card_id, e)
            return {"ok": False, "card_id": u.card_id, "error": str(e)}

    results = await asyncio.gather(*[_update(u) for u in updates])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def move_cards(moves: list[CardMove]) -> str:
    """Move one or more cards to a different list (e.g. To Do -> In Progress).

    Args:
        moves: List of moves. Each move requires card_id and the destination list_id.
    """
    log.info("move_cards count=%d", len(moves))

    async def _move(m: CardMove):
        try:
            result = await _request_json("PUT", f"/cards/{m.card_id}", {"idList": m.list_id})
            log.debug("move_cards: moved card %s to list %s", m.card_id, m.list_id)
            return {"ok": True, "card_id": m.card_id, "result": _strip_card(result)}
        except Exception as e:
            log.error("move_cards: failed to move card %s: %s", m.card_id, e)
            return {"ok": False, "card_id": m.card_id, "error": str(e)}

    results = await asyncio.gather(*[_move(m) for m in moves])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def delete_cards(card_ids: list[str]) -> str:
    """Permanently delete one or more cards.

    Args:
        card_ids: List of card IDs to delete.
    """
    log.info("delete_cards count=%d ids=%s", len(card_ids), card_ids)

    async def _delete(card_id: str):
        try:
            result = await _request_json("DELETE", f"/cards/{card_id}")
            log.debug("delete_cards: deleted card %s", card_id)
            return {"ok": True, "card_id": card_id, "result": result}
        except Exception as e:
            log.error("delete_cards: failed to delete card %s: %s", card_id, e)
            return {"ok": False, "card_id": card_id, "error": str(e)}

    results = await asyncio.gather(*[_delete(cid) for cid in card_ids])
    return json.dumps(list(results), indent=2)


# ── Checklists ──────────────────────────────────────────────────────────────


@mcp.tool()
async def create_checklists(checklists: list[ChecklistInput]) -> str:
    """Add one or more checklists to cards.

    Args:
        checklists: List of checklists to create. Each requires card_id and name.
    """
    log.info("create_checklists count=%d", len(checklists))

    async def _create(cl: ChecklistInput):
        try:
            result = await _request_json("POST", "/checklists", {"idCard": cl.card_id, "name": cl.name})
            log.debug("create_checklists: created %r on card %s", cl.name, cl.card_id)
            return {"ok": True, "card_id": cl.card_id, "name": cl.name, "result": result}
        except Exception as e:
            log.error("create_checklists: failed for card %s: %s", cl.card_id, e)
            return {"ok": False, "card_id": cl.card_id, "name": cl.name, "error": str(e)}

    results = await asyncio.gather(*[_create(cl) for cl in checklists])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def add_checklist_items(items: list[ChecklistItemInput]) -> str:
    """Add one or more items to checklists.

    Args:
        items: List of items to add. Each requires checklist_id and name.
    """
    log.info("add_checklist_items count=%d", len(items))

    async def _add(item: ChecklistItemInput):
        try:
            result = await _request_json(
                "POST", f"/checklists/{item.checklist_id}/checkItems", {"name": item.name}
            )
            log.debug("add_checklist_items: added %r to checklist %s", item.name, item.checklist_id)
            return {"ok": True, "checklist_id": item.checklist_id, "name": item.name, "result": result}
        except Exception as e:
            log.error("add_checklist_items: failed for checklist %s: %s", item.checklist_id, e)
            return {"ok": False, "checklist_id": item.checklist_id, "name": item.name, "error": str(e)}

    results = await asyncio.gather(*[_add(item) for item in items])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def update_checklists(updates: list[ChecklistUpdate]) -> str:
    """Update one or more checklists' name and/or move them to another card.

    Args:
        updates: List of updates. Each requires checklist_id; name and card_id are optional.
                - name: renames the checklist
                - card_id: moves the checklist to another card (Trello uses idCard)
    """
    log.info("update_checklists count=%d", len(updates))

    async def _update(u: ChecklistUpdate):
        try:
            params: dict[str, str] = {}
            if u.name:
                params["name"] = u.name
            if u.card_id:
                params["idCard"] = u.card_id
            result = await _request_json("PUT", f"/checklists/{u.checklist_id}", params)
            log.debug("update_checklists: updated checklist %s fields=%s", u.checklist_id, list(params.keys()))
            return {"ok": True, "checklist_id": u.checklist_id, "result": result}
        except Exception as e:
            log.error("update_checklists: failed checklist %s: %s", u.checklist_id, e)
            return {"ok": False, "checklist_id": u.checklist_id, "error": str(e)}

    results = await asyncio.gather(*[_update(u) for u in updates])
    return json.dumps(list(results), indent=2)


@mcp.tool()
async def delete_checklists(deletes: list[ChecklistDelete]) -> str:
    """Delete one or more checklists.

    Args:
        deletes: List of deletions. Each requires checklist_id.
    """
    log.info("delete_checklists count=%d", len(deletes))

    async def _delete(d: ChecklistDelete):
        try:
            result = await _request_json("DELETE", f"/checklists/{d.checklist_id}")
            log.debug("delete_checklists: deleted checklist %s", d.checklist_id)
            return {"ok": True, "checklist_id": d.checklist_id, "result": result}
        except Exception as e:
            log.error("delete_checklists: failed checklist %s: %s", d.checklist_id, e)
            return {"ok": False, "checklist_id": d.checklist_id, "error": str(e)}

    results = await asyncio.gather(*[_delete(d) for d in deletes])
    return json.dumps(list(results), indent=2)


# ── Comments ────────────────────────────────────────────────────────────────


@mcp.tool()
async def add_comments(comments: list[CardComment]) -> str:
    """Add one or more comments to cards.

    Args:
        comments: List of comments to add. Each requires card_id and text.
    """
    log.info("add_comments count=%d", len(comments))

    async def _add(c: CardComment):
        try:
            result = await _request_json(
                "POST", f"/cards/{c.card_id}/actions/comments", {"text": c.text}
            )
            log.debug("add_comments: commented on card %s", c.card_id)
            return {"ok": True, "card_id": c.card_id, "result": result}
        except Exception as e:
            log.error("add_comments: failed for card %s: %s", c.card_id, e)
            return {"ok": False, "card_id": c.card_id, "error": str(e)}

    results = await asyncio.gather(*[_add(c) for c in comments])
    return json.dumps(list(results), indent=2)


# ── Search ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def search_cards(query: str) -> str:
    """Search for cards by keyword on the board, excluding the Archive list.

    Args:
        query: Search term to look for.
    """
    log.info("search_cards query=%r", query)
    data, archive_id = await asyncio.gather(
        _request_json("GET", "/search", {"query": query, "idBoards": _board_id(), "modelTypes": "cards", "cards_filter": "open"}),
        _get_archive_list_id(),
    )
    if archive_id and "cards" in data:
        before = len(data["cards"])
        data["cards"] = [c for c in data["cards"] if c.get("idList") != archive_id]
        log.debug("search_cards: filtered %d archive cards, returning %d", before - len(data["cards"]), len(data["cards"]))
    if "cards" in data:
        data["cards"] = [_strip_card(c) for c in data["cards"]]
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "http":
        import uvicorn
        app = mcp.streamable_http_app()
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8000")))
    elif transport == "sse":
        import uvicorn
        app = mcp.sse_app()
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("MCP_PORT", "8000")))
    else:
        mcp.run(transport="stdio")
