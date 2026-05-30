# Requirements

## Overview

`telegram-calendar-bot` is a Telegram bot that converts natural-language descriptions of events into Google Calendar "add event" links. The bot accepts free-form text (e.g. "tomorrow 10am meeting with John for 40 minutes"), uses a large-language model (LLM) to extract structured event data, and replies with a direct link that opens the Google Calendar event creation dialog pre-filled with the parsed details.

---

## Functional Requirements

### FR-1 — Message Intake

| ID | Requirement |
|----|-------------|
| FR-1.1 | The bot MUST accept plain-text messages in any language that describe a single event and a time. |
| FR-1.2 | The bot MUST accept messages that contain only a Telegram caption (i.e. images/videos with caption text). |
| FR-1.3 | The bot MUST accept messages that are replies to another message; in that case the replied-to message text is prepended to the input as discussion context. |
| FR-1.4 | The bot MUST reject (with an informative error reply) messages whose non-whitespace content is empty after combining text and reply context. |
| FR-1.5 | User input MUST be truncated to `MAX_INPUT_LENGTH` characters before being forwarded to the LLM. |

### FR-2 — LLM Integration

| ID | Requirement |
|----|-------------|
| FR-2.1 | The bot MUST call an OpenAI-compatible chat-completion API (configurable endpoint). |
| FR-2.2 | The bot MUST send a prompt built from a configurable template (`prompt_template.txt`) that injects `{content}` (user text) and `{now}` (current ISO-8601 datetime + weekday name). |
| FR-2.3 | The LLM MUST return a JSON object with the following fields: `text` (event title), `location` (venue or empty string), `start` (ISO-8601 datetime of the event start, UTC), `duration` (compact string in `XdYhZm` format). |
| FR-2.4 | The bot MUST stream the LLM response and accumulate tokens. |
| FR-2.5 | If the LLM call fails or returns no content, the bot MUST reply with a descriptive error message. |
| FR-2.6 | If the accumulated response cannot be parsed as valid JSON, the bot MUST reply with the raw output and a descriptive error message. |

### FR-3 — Calendar Link Generation

| ID | Requirement |
|----|-------------|
| FR-3.1 | From the parsed JSON, the bot MUST compute the event end time as `start + duration`. |
| FR-3.2 | The bot MUST construct a Google Calendar "add event" URL using `start` and `end` in `YYYYMMDDTHHMMSSz` format. |
| FR-3.3 | The URL MUST carry the event title (`text`), time range (`dates`), location, and a short details field containing the original user input (truncated to 200 characters) plus an attribution note. |
| FR-3.4 | The final message sent to the user MUST contain both the raw JSON from the LLM and the Google Calendar URL. |

### FR-4 — Access Control

| ID | Requirement |
|----|-------------|
| FR-4.1 | The bot MUST maintain a whitelist of allowed Telegram user IDs (`ALLOWED_TELEGRAM_USER_IDS`). |
| FR-4.2 | The bot MUST maintain a separate list of admin user IDs (`ADMIN_USER_IDS`); this list is optional and defaults to empty. |
| FR-4.3 | In **private chats**, only users whose ID appears in `ALLOWED_TELEGRAM_USER_IDS` or `ADMIN_USER_IDS` MAY use the bot; all others MUST receive a "Permission denied" reply and the message MUST NOT be processed further. |
| FR-4.4 | In **group and supergroup chats**, all members MAY send messages to the bot without explicit whitelisting. |
| FR-4.5 | Admin users MUST see an additional note in the `/help` and `/start` replies indicating that admin commands are available. |

### FR-5 — Bot Commands

| ID | Requirement |
|----|-------------|
| FR-5.1 | `/start` and `/help` MUST reply with a brief description of the bot and register the command list with BotFather. |
| FR-5.2 | `/new` MUST trigger the same event-creation pipeline as a plain-text message. |

### FR-6 — Rate Limiting

| ID | Requirement |
|----|-------------|
| FR-6.1 | The bot MUST NOT send more than **1 Telegram API message per second** to the same chat (per Telegram Bot API guidelines). |
| FR-6.2 | The bot MUST NOT send more than **19 messages per rolling 60-second window** across all chats. |
| FR-6.3 | Rate-limiting MUST NOT block the asyncio event loop; waiting MUST be implemented with async sleep. |

---

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | All secret credentials (bot token, API key, allowed user IDs) MUST be loaded exclusively from a `.env` file; system environment variables MUST NOT leak into the process. |
| NFR-2 | The bot MUST be deployable as a Docker container. A multi-stage `Dockerfile` MUST provide separate `production` and `test` build targets. |
| NFR-3 | All unit and integration tests MUST be executable inside Docker (`docker compose --profile test run --rm test`). |
| NFR-4 | The codebase MUST include a test suite (pytest) covering: duration parsing, throttle logic, permission checks, message handling, and LLM API response processing. |
| NFR-5 | I/O with the Telegram API and OpenAI API MUST be fully asynchronous (no blocking calls on the event loop). |
| NFR-6 | Configuration MUST be done entirely through environment variables and the two mountable files (`.env`, `prompt_template.txt`). |

---

## Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram Bot API token obtained from BotFather. |
| `OPENAI_API_KEY` | Yes | — | API key for the OpenAI-compatible endpoint. |
| `LLM_MODEL` | Yes | — | Model name to pass to the chat-completion API (e.g. `gpt-4o`). |
| `OPENAI_API_URL` | No | `https://api.openai.com/v1/` | Base URL for the OpenAI-compatible API. |
| `ALLOWED_TELEGRAM_USER_IDS` | Yes | — | Comma-separated Telegram user IDs permitted to use the bot in private chats. |
| `ADMIN_USER_IDS` | No | _(empty)_ | Comma-separated Telegram user IDs with admin privileges. |
| `MAX_INPUT_LENGTH` | No | `2000` | Maximum number of characters of user content forwarded to the LLM. |

---

## Duration Format

The LLM is instructed to return durations in the compact format `XdYhZm`, where:
- `X` = whole days
- `Y` = whole hours (remainder after days)
- `Z` = whole minutes (remainder after hours)

Any component may be omitted when zero (e.g. `2h`, `45m`, `1d3h12m`). The parser MUST treat missing components as zero.

---

## System Context Diagram

```
User (Telegram) ──text──► Bot (telegram-calendar-bot)
                                      │
                           ┌──────────▼──────────┐
                           │  Permission check    │
                           └──────────┬──────────┘
                                      │ allowed
                           ┌──────────▼──────────┐
                           │  Prompt construction  │
                           │  (prompt_template.txt)│
                           └──────────┬──────────┘
                                      │
                           ┌──────────▼──────────┐
                           │  LLM API (OpenAI)    │
                           └──────────┬──────────┘
                                      │ JSON response
                           ┌──────────▼──────────┐
                           │  Calendar URL builder │
                           └──────────┬──────────┘
                                      │
                         Reply with JSON + URL ──► User
```
