# Observability for AI agents (BacktobasicsPython)

This file mirrors what `grafana-assistant agents-md <this-repo>` is intended to produce: enough context for an agent to reason about this stack in Grafana / Prometheus without opening large dashboard JSON in the model context.

## Endpoints (docker-compose)

| Service    | URL                    |
| ---------- | ---------------------- |
| Grafana    | http://localhost:3000  |
| Prometheus | http://localhost:9090  |
| API        | http://localhost:5000  |

## Dashboard (summary, not full JSON)

- **Title:** Backtobasics — Métriques
- **UID:** `backtobasics-metrics` (provisioning: `monitoring/grafana/dashboards/backtobasics.json`)
- **Datasource:** Prometheus, UID `prometheus`
- **Panels (what to use each for):** HTTP throughput and status; latency p50/p90/p99; Celery task counts by status and task duration p99; ML inference p50/p90/p99; mask confidence mean/p90

Prefer asking Grafana tools for a **summary** or a **single property** (see Grafana Assistant rule) instead of loading the full dashboard model into chat.

## Metrics implemented in code

- `http_requests_total`, `http_request_duration_seconds_*` (instrumentator)
- `celery_task_duration_seconds_*`, `celery_tasks_total{status="success|failure"}` — see `project/src/infrastructure/metrics.py`
- `ml_inference_duration_seconds_*`, `ml_mask_confidence_*`

**Sanity check:** if `celery_tasks_total` is missing in Prometheus’ `/api/v1/label/__name__/values` while the worker is running, tasks may be failing before the success/failure `inc()` in `celery/tasks.py` (e.g. missing MinIO object); use logs and the Celery / API panels together.

## Grafana Assistant CLI (after install)

1. Install: [grafana/assistant-cli](https://github.com/grafana/assistant-cli) (the workspace skill does not auto-install the binary).
2. Point at this Grafana, authenticate, then run one-shot investigation prompts from the project directory:

   ```bash
   grafana-assistant config set-instance local --url http://localhost:3000
   grafana-assistant auth
   grafana-assistant prompt "In datasource prometheus, is http_requests_total non-zero in the last hour? List series by handler if any."
   ```

Use `grafana-assistant prompt "..." --json` and `-c <contextId>` for follow-up questions in the same conversation (see the grafana-assistant CLI skill).

## Why this is useful here

- The **Grafana rule** in Cursor steers tools toward **summaries and targeted properties** so dashboard JSON does not bloat the context window.
- The **CLI skill** documents how to run **read-only** investigations (PromQL, logs, panel search) against *your* Grafana from the repo, with optional **tunnel** to local project files when you need filesystem context.

When Grafana MCP is enabled in Cursor, the same ideas apply: `search_dashboards` → `get_dashboard_summary` / `get_dashboard_property` with JSONPath, and `generate_deeplink` for shareable links instead of narrating menu clicks.
