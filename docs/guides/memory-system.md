# Memory System

ProwlrBot's memory system provides persistent, auto-compacting context that survives across conversations. The agent can recall past interactions, facts you've told it, and decisions made in previous sessions.

---

## Architecture

```
ProwlrBotInMemoryMemory
    │
    ├── short-term buffer     (current session messages)
    │
    └── MemoryManager
            │
            ├── compaction trigger (when token budget exceeded)
            ├── persistent store   (~/.prowlrbot/memory/)
            └── search index       (semantic retrieval)
```

The memory system is implemented in `src/prowlrbot/agents/memory/`. Key classes:

- `ProwlrBotInMemoryMemory` — extends AgentScope's memory, adds budget tracking
- `MemoryManager` — handles persistence, compaction, and retrieval

---

## Token budget and auto-compaction

Every message added to memory is counted against a token budget. The default budget is derived from the active model's context window (configurable via `max_input_length` in `config.json`, default 128K tokens).

When the budget is exceeded, the `MemoryManager` compacts older messages:

1. Summarizes the oldest `N` messages into a condensed form
2. Stores the condensed summary in persistent memory
3. Removes the original messages from the short-term buffer

This keeps the agent context within the model's limits while retaining the essential information.

---

## Configuring memory limits

In `~/.prowlrbot/config.json`:

```json
{
  "agents": {
    "running": {
      "max_iters": 50,
      "max_input_length": 131072
    }
  }
}
```

`max_input_length` is in tokens. Common values:
- GPT-4o: 128K → `131072`
- Claude Sonnet: 200K → `204800`
- Llama 3.1 8B (Ollama): 8K → `8192`
- Mistral 7B (llama.cpp): 32K → `32768`

---

## Memory search tool

The agent has access to a `memory_search` built-in tool that can search across stored memories:

```
User: What was the deployment plan we discussed last week?
Agent: [calls memory_search with "deployment plan"]
Agent: Based on our conversation on 2026-03-06, we decided to...
```

The search tool is in `src/prowlrbot/agents/tools/` and uses the `MemoryManager`'s search index.

---

## Session isolation

Each channel + user combination gets its own session. Sessions are identified by `session_id` (defaults to a combination of channel and user ID).

Memory is per-session: the agent running in your Discord DM has separate memory from the agent running in the console or a Telegram chat.

---

## Persistence locations

| Path | Contains |
|------|---------|
| `~/.prowlrbot/chats/` | Full chat history (JSON files per session) |
| `~/.prowlrbot/memory/` | Compacted memory summaries |

---

## Exporting and clearing memory

```bash
# Export all chat history
prowlr export chats

# Delete chat history older than 30 days
prowlr export retention --days 30

# Preview what would be deleted
prowlr export retention --days 30 --dry-run

# Full export (config + chats + skills)
prowlr export all
prowlr export all --format json
```

---

## How `ChatManager` and `MemoryManager` interact

`ChatManager` (in `src/prowlrbot/app/`) handles chat persistence — reading/writing session history to `~/.prowlrbot/chats/`. It stores the raw message log.

`MemoryManager` handles the agent's working memory — what gets injected into the model's context for the current query. When a session grows too long:

1. `MemoryManager.maybe_compact()` is called
2. Old messages are summarized using the LLM
3. The summary is stored and old messages are pruned
4. The agent's next query gets the compacted context

---

## Disabling memory

To run the agent statelessly (no memory across turns), you can clear history between sessions via the API:

```bash
curl -X DELETE http://localhost:8088/api/sessions/SESSION_ID
```

Or set a very short retention:

```bash
prowlr export retention --days 0
```

This is useful for testing or for agent configurations where you explicitly want no context carryover.
