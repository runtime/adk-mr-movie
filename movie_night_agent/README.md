# 🎬 Mr. Movie — Multi-Agent Movie Night Assistant

### Mr. Movie is a multi-agent, stateful movie assistant built with Google ADK, designed to help users remember what they’ve watched, track what they’re watching, and discover new movies using external data sources like TMDB.

This project focuses on deterministic memory, clear agent responsibilities, and extensible architecture — not prompt hacks.

---


## 🧠 Core Concepts

LLMs do not “own” memory — tools do

State lives in a database, not in the model

Agents are specialists, coordinated by a root agent

External APIs are tools, never free-form hallucinations

---

## 🏗️ Architecture Diagram

```python
User (CLI / future UI)
        |
        v
┌───────────────────────┐
│   Root Agent (LLM)    │
│  "Mr. Movie"          │
│  - Conversation flow  │
│  - Routing            │
│  - Context awareness  │
└─────────┬─────────────┘
          │
          │ Tool Calls
          ▼
┌──────────────────┐        ┌──────────────────────┐
│  Memory Agent    │        │  Research Agent      │
│  (Deterministic) │        │  (TMDB Read-Only)    │
│                  │        │                      │
│ - seen_movies    │        │ - search movie       │
│ - current_movies │        │ - fetch details      │
│ - user_name      │        │                      │
└─────────┬────────┘        └─────────┬────────────┘
          │                           │
          ▼                           ▼
     SQLite DB                  TMDB API

```
---
## 🧑🏻‍💻 Repo Directory

```python
adk-mr-movie/
│
├── movie_night_agent/
│   ├── main.py                 # CLI entrypoint
│   ├── agent.py                # Root LLM agent
│   │
│   ├── models/
│   │   ├── movie.py             # Pydantic Movie schema
│   │   └── __init__.py
│   │
│   ├── subagents/
│   │   ├── memory_agent/
│   │   │   └── agent.py         # Persistent memory tools
│   │   ├── research_agent/
│   │   │   ├── agent.py         # TMDB-facing agent
│   │   │   └── tmdb.py          # TMDB API helpers
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── call_agent_async.py  # Runner + event aggregation
│   │   ├── console.py           # CLI formatting
│   │   └── events.py            # RunResult abstraction
│   │
│   └── __init__.py
│
├── pyproject.toml
├── .env
└── README.md

```
---

## 🧩 Implemented Agents
### 🎥 Root Agent (agent.py)

* Conversational control
* Routes tasks to sub-agents
* Maintains awareness of user state
* Never mutates state directly


### 🧠 Memory Agent

#### Purpose: deterministic state management

#### Capabilities:

* Store and retrieve:
  - user_name 
  - seen_movies 
  - current_movies 
  - Deduplication via stable internal IDs 
  - Pydantic-validated movie objects


* Memory lives in:
  - SQLite via ADK DatabaseSessionService

###  🔍 Research Agent (TMDB)
#### Purpose: enrich movies with real data

#### Capabilities:

* Search movies by title
* Fetch full metadata by TMDB ID
* Read-only access via TMDB v3 API
* Normalizes external data into internal schema
* The LLM must call this agent when data is missing — it cannot invent movie metadata.

---
### 🎞️ Movie Data Model (Pydantic)

Movies are stored using a vendor-agnostic internal ID, with provider data nested inside:
```{
  "id": "title:apocalypse-now",
  "title": "Apocalypse Now",
  "year": 1979,
  "providers": {
    "tmdb": {
      "id": 28,
      "rating": 8.3,
      "poster_url": "...",
      "raw": {...}
    }
  }
}
```
---
### 🔮 Movie DB agnostic - the system is open to:
currently we are using tmdb but we can plug and play any movie db in the future 

- IMDb
- JustWatch
- Google Search
- Future internal ranking systems

---
### 🚀 How to Run (CLI)
1. Activate virtual environment

`source .venv/bin/activate`

2. Install package (editable)

`pip install -e .
`

3. Set environment variables (.env)
`TMDB_READ_ACCESS_TOKEN=your_read_token_here
`
4. Run the app
`python -m movie_night_agent.main
`
---

### 🧪 Example Interaction
#### You:

`hi im juliana`

→ memory_agent.update_user_name

#### You:

`i have seen apocalypse now
`

→ research_agent.search_movie

→ research_agent.movie_details

→ memory_agent.add_seen_movie

#### You:
`what movies have i seen?`

→ memory_agent.view_seen_movies


👉🏼 Tool calls are visible in result.tool_calls for inspection and debugging.

---

### 🧭 Design Principles
i have designed this system with the following principles

- State > Prompts
- Tools > Hallucinations
- Schemas > Strings
- Extensibility > Cleverness


---

### Design Pattern
main.py
 - CREATES SESSION
 - INITIAL STATE
 - RUNNER

Runner loads agent and session service
user requests are handled by the runner
runner sends request to agent 

utils/*
 - utils.call_agent_async (runner, user_id, session_id, query)
runner looks through session for events
 - utils.process_agent_response 
runner loops through events to set session state
 - utils.colors is color scheme for agent response in cli
 - utils.console are helper functions for cli output

---

### 🛣️ Roadmap (Planned)

#### 🎨 Presentation Agent (Markdown / Cards)

#### 📺 Streaming availability (JustWatch)

#### 🌦️ Contextual recommendations (time, weather)

#### 🧠 Long-term conversation memory (Vertex / embeddings)

#### 🌐 Web UI

---

## 🧑‍💻 Status

### Current state:
✔ Stable

✔ Persistent memory

✔ External data enrichment

✔ Multi-agent routing confirmed


---

# Apendix

### 📚 Research:
#### Docs
internal and external tool best practices:
https://google.github.io/adk-docs/tools/built-in-tools/#use-built-in-tools-with-other-tools

session.state

https://google.github.io/adk-docs/tools-custom/#state-management

session services:
https://google.github.io/adk-docs/sessions/session/#sessionservice-implementations

#### videos
best adk video: https://www.youtube.com/watch?v=P4VFL9nIaIA

### pocs
originally this project supported multiple agent memory types based off a runner and using internal and db sessions. those have been deleted and are lost. the only poc to this would be the adk movie night agent project which doesn't actually have the steps leadig to this. Below are the pocs the former agent supported for reference to how we got to dbsessionservice

👉🏼 ****: 
**DataBaseMemoryService** POC - LLM that save movies the user has seen and recall them during that session

to run:
```
python movie-night-agent/persistent_storage_main.py
```
👉🏼 **InMemorySessionService**:  not persistent
:
 basic_stateful_session uses inMemory but no db so no persistent storage

to run:
```
python movie-night-agent/basic_stateful_sessionent.py
```

⚠️ Files not in use:

**tools** contains several commented out pocs
- use a tool- see hello_tool.py

**to run:**

```
python movie-night-agent/agent.py

```

### POC checklist
small rocks in agent and other files we needed in order to make Mr. Movie
- root agent llm
  - with external tool
  - with internal tool
- structured output
  - output_schema
- state
  - session.state[output_key]
- storage
  - DatabaseMemoryService

  

### DB
db is sql lite and resides locally.
you can find the data saved in the session in the 'sessions' table.
the app doesn't load the data if it exists
### todo
- root_agent -> LlmAgent 
- tools
  - hello_tool*
  - tmdb_tool
- subagents
  - search_agent
  - tmbd_agent
  - presentation_agent
- structured output
  - output_schema
- state
 
- runners
  - need poc to prove multiple runner and session cleanup
  