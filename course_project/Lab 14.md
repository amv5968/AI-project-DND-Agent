# AI Dungeon Master — Project Report

## 1. Base System Functionality

The AI Dungeon Master is a conversational AI system that acts as a real-time Dungeons & Dragons Dungeon Master. It is accessible through two entry points: a **Streamlit web UI** (`streamlit_app.py`) and a **console CLI** (`cli.py`). The system integrates an Ollama-hosted LLM, ChromaDB-backed RAG, SQLite turn memory, deterministic tool calls, multi-step planning, text-to-speech narration, scene image generation, and a Monte Carlo reinforcement learning agent for adaptive temperature selection.

### Supported Scenarios

| Scenario Key | Description |
|---|---|
| `tavern_social` | Social encounters with NPCs in a tavern setting. The DM narrates NPC motives, hidden agendas, and rewards roleplay through dialogue. |
| `dungeon_exploration` | Room-by-room dungeon exploration with sensory descriptions, interactable objects, traps, and route choices. |
| `combat_resolution` | Turn-based combat with initiative, attack rolls via `roll_d20`, hit/miss outcomes, and tracking of temporary effects like poison or fear. |
| `merchant_bargain` | Complex NPC merchant interactions with bargaining, persuasion checks, and deceptive characters. |
| `quest_tracking` | Maintains quest objectives, updates quest status in SQLite, and weaves unresolved threads into ongoing narration. |
| `console_campaign` | General-purpose CLI campaign mode that combines all scenarios in a free-form text session. |

The system runs without errors across both interfaces. All responses are grounded in the session's conversation history and retrieved lore context, ensuring continuity across turns.


---
## 2. Prompt Engineering and Model Parameter Choice

### System Prompt Template

The DM's behavior is driven by a **role-based system prompt** loaded from `templates/dm_system_template.json`. The template uses `{{placeholder}}` substitution to inject three dynamic pieces of context at runtime:

```
You are the Dungeon Master for a Dungeons and Dragons campaign.

Scenario: {{scenario}}

Recent History:
{{recent_history}}

Relevant Lore Context:
{{context_text}}

Rules for your response:
1. Stay in DM voice with vivid but concise narration.
2. Respect tool outputs if a roll/coin result is provided by the user context.
3. End each response with 2–3 concrete choices for what players can do next.
4. Keep continuity with recent history and quest status.
5. If context is missing, make a reasonable assumption and say it clearly.
```

- **`{{scenario}}`** — sets the active scenario so the LLM adjusts its narration style (combat is terse and urgent; tavern social is conversational).
- **`{{recent_history}}`** — the last 8 turns from SQLite, giving the model short-term conversational memory.
- **`{{context_text}}`** — the top-3 ChromaDB lore chunks most relevant to the player's current message.

The prompt is loaded by `prompts.py` using `load_system_prompt`, which reads the JSON and applies `insert_params` substitution.

### Parameter Rationale

| Parameter | Default | Rationale |
|---|---|---|
| `temperature` | 0.4 (RL-adaptive) | Low enough for coherent narrative continuity; the RL agent adaptively tunes this per scenario based on player engagement. The Streamlit slider allows manual override (0.0–1.0). |
| `top_p` | 0.9 | Nucleus sampling keeps outputs diverse without drifting into incoherence. |
| `max_tokens` | 500 | Keeps DM responses concise and action-focused; slider allows up to 1200 for elaborate scenes. |
| `num_context_chunks` | 3 | Balances lore coverage against prompt length; retrieves the three most relevant lore passages. |

Temperature is also managed by the **RL agent** (see Section 6): across sessions, the Monte Carlo agent learns which temperature setting produces the most engaged responses for each scenario and turn stage, removing the need to hand-tune this parameter scenario by scenario.



---
## 3. Tools Usage

Tools are implemented in `tools.py` and invoked automatically by the engine in `_run_tools` before the LLM call. Their results are prepended to the user message so the model can reference them in its narration.

### `roll_d20(skill, dc, player)`

Simulates a d20 skill check. Called when the player types a `/roll` command:

```
/roll player=Aria skill=stealth dc=14
```

The tool parses the parameters with `parse_roll_request`, rolls a random integer 1–20, compares against the DC, and returns a structured result including a `narration` string:

> "Aria rolled 17 for stealth against DC 14 and got a success."

This narration is injected into the user message as `Tool[roll_d20]: ...`, so the LLM narrates the consequence rather than deciding the outcome itself.

### `coin_flip()`

Called when the player types `/flip`. Returns heads or tails with a narration string. Used for binary fate decisions in social and exploration scenarios.

### `GameStateDB` (SQLite tool)

`database.py` provides a persistent SQLite store with two tables:

- **`turns`** — logs every user and assistant message with session ID, role, message text, scenario, and timestamp. Enables the DM to recall the last 8 turns as grounded short-term memory.
- **`quests`** — stores quest name, status (`active`, `complete`, `failed`), and notes per session. Updated via `set_quest_status` and surfaced in the planning context.