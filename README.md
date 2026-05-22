# Deep Research Agent

A multi-agent research assistant that searches the web and academic papers in parallel, synthesizes results into a cited answer, and self-evaluates its output using an LLM-powered critic loop — all streamed in real time over a FastAPI backend.

---

## Overview

Deep Research Agent accepts a natural-language research query and routes it through a graph of specialized AI agents orchestrated by [LangGraph](https://github.com/langchain-ai/langgraph). Rather than issuing a single LLM call, the system decomposes the query into a task plan, dispatches multiple agents concurrently, synthesizes their findings into a cited answer, and then runs a structured critic evaluation — retrying up to three times if the answer doesn't meet quality thresholds.

```
                      ┌──────────────────────────────┐
                      │         Planner Agent        │
                      │  (query → execution plan)    │
                      └──────────────┬───────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
     ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
     │ Web Search Agent │  │ Academic Search  │  │   Code Agent     │
     │     (Tavily)     │  │    (OpenAlex)    │  │                  │
     └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
              └─────────────────────┬─────────────────────┘
                                    ▼
                           ┌──────────────────┐
                           │   Synthesizer    │◄────|
                           │ (cited answer)   │     |
                           └────────┬─────────┘     |
                                    ▼               |retry (up to 3×)
                           ┌──────────────────┐     |
                           │  Critic Agent    │     |
                           │  (eval scores)   │────►|
                           └────────┬─────────┘
                                    │ pass
                                    ▼
                           ┌──────────────────┐
                           │    Finalize      │
                           └──────────────────┘
```

Every step is streamed back to the client as a Server-Sent Event, and the full pipeline run is traced in Langfuse.

---

## Features

**Multi-agent parallelism.** The planner produces an execution plan that assigns each sub-task to a specific agent. LangGraph's `Send` API dispatches web search, academic search, and code tasks concurrently, so multiple sources are gathered in a single pass rather than sequentially.

**Structured query planning.** Before any search happens, the LLM classifies the query complexity (`simple`, `moderate`, or `complex`) and produces a typed `ExecutionPlan` — a list of `AgentTask` objects, each with an assigned agent, a sub-query, and the reasoning behind the agent choice. This makes the planning step auditable.

**Academic + web coverage.** The web search agent uses Tavily to retrieve pages from blogs, documentation, forums, and news sources, scoring each result for relevance. The academic search agent queries the free OpenAlex API for peer-reviewed works, extracting title, authors, year, abstract, and key findings from each paper.

**Structured critic evaluation.** After synthesis, a dedicated critic agent scores the answer on four independent axes — faithfulness to the evidence, relevance to the query, completeness, and overall quality — all as 0–1 floats. If `should_retry` is true and fewer than three retries have occurred, the graph loops back to the synthesizer with the critic's detailed feedback in the conversation history, allowing the next synthesis to address the specific weaknesses identified.

**Cited answers.** Every synthesized answer includes a typed list of `Citation` objects (position, title, URL, source type), formatted in the SSE stream for easy display.

**Real-time SSE streaming.** The API streams node-level progress events (`planner_agent`, `web_search_agent`, etc.) as each step completes, followed by the final formatted answer. Clients can show a live progress indicator without polling.

**Full observability with Langfuse.** Every pipeline run is decorated with `@observe` and enriched with the query as a span name, giving you full traces, scores, and latency breakdowns in the Langfuse dashboard.

**Docker support.** The whole stack — including all Python dependencies — is containerized and runs with a single `docker compose up`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| LLM | DeepSeek (`deepseek-v4-flash`) |
| Web search | Tavily |
| Academic search | OpenAlex |
| Structured outputs | Instructor + Pydantic v2 |
| API server | FastAPI + Uvicorn |
| Observability / tracing | Langfuse |
| Containerization | Docker / Docker Compose |
| Language | Python 3.12 |

---

## Project Structure

```
deep-research-agent/
│
├── agents/
│   ├── planner.py            # Decomposes the query into an ExecutionPlan
│   ├── web_search.py         # Searches the web via Tavily; scores results for relevance
│   ├── academic_search.py    # Queries OpenAlex for peer-reviewed papers
│   └── code_agent.py         # Generates and explains code relevant to the query
│
├── nodes/
│   ├── synthesizer.py        # Merges all search results into a SynthesizedAnswer with citations
│   └── critic.py             # Scores the answer and sets should_retry; passes feedback back
│
├── static/
│   └── index.html            # Single-page frontend served by FastAPI
│
├── api.py                    # FastAPI app — POST /research returns an SSE stream
├── graph.py                  # LangGraph StateGraph: nodes, edges, conditional routing
├── schemas.py                # All Pydantic models and the AgentState TypedDict
├── prompts.py                # LLM prompt templates for each agent/node
├── llm_client.py             # DeepSeek LLM client (LangChain-OpenAI compatible)
├── config.py                 # Loads and validates environment variables
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

---

## Data Models

The pipeline state is fully typed. Here are the key schemas defined in `schemas.py`:

**`AgentTask`** — a single unit of work dispatched to one agent, with a sub-query and the planner's reasoning for the agent choice.

**`ExecutionPlan`** — the planner's output: a list of `AgentTask` objects plus a query complexity label (`simple` / `moderate` / `complex`).

**`WebSearchResult`** — a single Tavily result: URL, title, content, source type (blog/docs/forum/news/other), and a 0–1 relevancy score.

**`AcademicSearchResult`** — an OpenAlex paper: title, authors, publication year, abstract, URL, and a list of extracted key findings.

**`CodeResult`** — generated code with language label and a plain-English explanation.

**`Citation`** — a numbered reference with title, URL, and source type (`web` / `academic` / `code`), used to build the answer's bibliography.

**`SynthesizedAnswer`** — the answer text, its citations list, and a 0–1 confidence score from the synthesizer.

**`EvalResult`** — the critic's output: four 0–1 scores (faithfulness, answer relevance, answer completeness, overall), a `should_retry` boolean, and a detailed reasoning string fed back into the conversation history on retry.

**`AgentState`** — the LangGraph state shared across all nodes, holding the query, execution plan, accumulated web/academic results (using `operator.add` for parallel merges), synthesized answer, eval result, retry count, final answer, and conversation history.

---

## Getting Started

### Prerequisites

- Python 3.12 (or Docker)
- API keys for DeepSeek, Tavily, and Langfuse (public + secret key)

### 1. Clone the repository

```bash
git clone https://github.com/dogukansagir/deep-research-agent.git
cd deep-research-agent
```

### 2. Configure environment variables

Create a `.env` file in the project root. All four variables below are required — the application will raise a `ValueError` at startup if any are missing:

```env
# LLM
DEEPSEEK_API_KEY=your_deepseek_api_key

# Web search
TAVILY_API_KEY=your_tavily_api_key

# Observability
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

Langfuse can be self-hosted or used via [cloud.langfuse.com](https://cloud.langfuse.com). The host is set to the cloud endpoint by default in `config.py` — change `LANGFUSE_HOST` there if you are self-hosting.

OpenAlex is queried without authentication, so no key is needed for academic search.

### 3a. Run with Docker (recommended)

```bash
docker compose up --build
```

### 3b. Run locally

```bash
pip install -r requirements.txt
uvicorn api:app --reload
```

The app will be available at `http://localhost:8000`. Open that URL in your browser to access the built-in frontend.

---

## API Reference

### `POST /research`

Starts a full research pipeline for the given query and streams progress back as Server-Sent Events.

**Request**

```http
POST /research
Content-Type: application/json

{
  "query": "What are the latest advances in quantum error correction?"
}
```

**Response** — `Content-Type: text/event-stream`

While the graph is running, one event is emitted per completed node, containing the node's name:

```
data: planner_agent

data: web_search_agent

data: academic_search_agent

data: synthesizer_agent

data: critic_agent

data: finalize
```

The final event contains the formatted answer and citations:

```
data: Answer: Quantum error correction has seen significant advances in... Citations: 1. Nature: Surface codes (...) | 2. arXiv: Fault-tolerant gates (...)
```

### `GET /`

Serves the built-in HTML frontend (`static/index.html`).

---

## How the Graph Works

The agent pipeline is a LangGraph `StateGraph` compiled in `graph.py`. Here is the full routing logic:

**Planner → parallel agents.** `planner_agent` is the entry point. Its output is fed into a `dispatch_agents` function that reads `state["execution_plan"].tasks` and issues a `Send` for each task to the appropriate node (`web_search_agent`, `academic_search_agent`, or `coding_agent`). All dispatched agents run concurrently; their results are merged into `web_results` and `academic_results` using `operator.add`, which safely accumulates lists from parallel branches.

**Parallel agents → synthesizer.** All three agent nodes have a direct edge to `synthesizer_agent`, so the synthesizer waits until all parallel work is complete before running.

**Synthesizer → critic.** The synthesizer always feeds into `critic_agent`.

**Critic → conditional routing.** A `retry_condition` function inspects `state["eval_result"].should_retry` and `state["retry_count"]`. If retry is requested and the count is below 3, the graph returns to `synthesizer_agent` (with the critic's feedback already in `conversation_history`). Otherwise it advances to `finalize`.

**Finalize → END.** The `finalize` node simply extracts the answer string from the synthesized answer and writes it to `state["final_answer"]`, then the graph terminates.

---

## Observability

All pipeline runs are instrumented with the `@observe` decorator from the Langfuse SDK. The span is named `research: <query>` so individual runs are easy to find in the Langfuse dashboard. From there you can inspect per-node latency, token usage, the critic's scores for each attempt, and the full conversation history across retries.

To view traces, log in to [cloud.langfuse.com](https://cloud.langfuse.com) (or your self-hosted instance) and navigate to the **Traces** tab.

---

## License

MIT — see [LICENSE](LICENSE) for details.
