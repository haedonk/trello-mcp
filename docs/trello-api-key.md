# How to get a Trello API key and token

You’ll need two things to use this server:

- **API key** (`TRELLO_API_KEY`)
- **API token** (`TRELLO_TOKEN`)

> Trello treats the “API key” as your application key, and the “token” as a user authorization token.

## 1) Get your Trello API key

1. Log in to Trello in your browser.
2. Open Trello’s developer Power-Ups admin page:
   - https://trello.com/power-ups/admin/
3. Create a new Power-Up / app if you don’t already have one.
4. In the left sidebar, select the **API Key** tab.
5. Generate/copy your **API key** from that page.

## 2) Generate a Trello token

1. Still on the **API Key** tab, find and click the **Token** hyperlink.
2. Approve the request and copy the generated token.

**Token format hint:** it’s usually a long token string (often starting with `A`).

## 3) Get your Board ID (optional)

Setting a default `TRELLO_BOARD_ID` is optional.

You can instead:
- Use `get_boards()` to retrieve boards and their IDs, then
- Call `set_board(board_id)` to set the active board for the current session.

If you do want a board ID up front, you can get it in a few ways:

- From the board URL (often the short ID is visible), or
- By listing your boards via the Trello API.

Example API call:

```bash
curl "https://api.trello.com/1/members/me/boards?fields=id,name,url&key=$TRELLO_API_KEY&token=$TRELLO_TOKEN"
```

## 4) Set environment variables

Required:

- `TRELLO_API_KEY`
- `TRELLO_TOKEN`

Optional:

- `TRELLO_BOARD_ID` (only needed if you want a default board without calling `set_board`)

Example (macOS/Linux):

```bash
export TRELLO_API_KEY="..."
export TRELLO_TOKEN="..."
# optional
export TRELLO_BOARD_ID="..."
```

Example (PowerShell):

```powershell
$env:TRELLO_API_KEY = "..."
$env:TRELLO_TOKEN = "..."
# optional
$env:TRELLO_BOARD_ID = "..."
```

## Security notes

- Don’t commit your key/token into git.
- Prefer putting them in your shell profile, secrets manager, or your MCP client’s secret store.
- If you believe your token was exposed, revoke it and generate a new one.
