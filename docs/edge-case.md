# Weekly Product Review Pulse — Edge & Corner Cases

This document outlines the known edge cases and potential failure modes across the system, along with how the architecture is designed to handle them.

---

## 1. Data Ingestion (Play Store MCP)

| Scenario | System Behavior | Mitigation |
|---|---|---|
| **Zero reviews in the time window** | The scraper returns an empty list. The orchestrator detects `len(reviews) == 0`. | Abort the run early with a clear `"No reviews found"` message. Do not generate an empty report or send an email. Record as `failed` (or skipped). |
| **Viral spike (too many reviews)** | 10,000+ reviews exist in the 8-12 week window. | The Play Store MCP respects `PLAYSTORE_MAX_REVIEWS` (e.g., 500). It sorts by "newest" or "relevance" to take a representative top-K sample, preventing OOM or massive LLM token bills. |
| **Play Store IP ban / Rate limiting** | Scraper receives HTTP 429 or connection reset. | Play Store MCP implements configurable throttling between batches. If blocked, MCP returns a structured error. Orchestrator retries 3x with exponential backoff before failing the run. |
| **Non-English or Emoji-only reviews** | User submits a review that is entirely emojis or in a language the embedding model struggles with. | Emojis are stripped *before* embeddings. Non-English reviews might cluster poorly if `all-MiniLM-L6-v2` isn't multilingual enough. **Future enhancement**: use a multilingual embedding model or filter by language `en` in the scraper. |
| **Malformed scraper data** | Google changes the Play Store HTML structure; scraper returns missing fields. | `PlayStoreReview` model uses `Optional` for fragile fields (e.g., `app_version`). If core fields (`text`, `rating`) are missing, the MCP server drops that specific review rather than failing the whole batch. |

---

## 2. Processing Pipeline (ML & LLM)

| Scenario | System Behavior | Mitigation |
|---|---|---|
| **Everything is Noise** | HDBSCAN assigns >80% of reviews to the noise bucket (`-1`). | If `< 2` valid clusters remain, the clustering module falls back to a "single-cluster" mode, treating all valid reviews as one overarching theme. |
| **LLM Hallucinates Quotes** | LLM generates a perfectly sensible quote that does not exist in the source text. | The `validator.py` step performs a fuzzy substring search of every quote against the original text. Hallucinated quotes are silently dropped. If *all* quotes are dropped, the report proceeds but notes "No verified quotes." |
| **LLM returns invalid JSON** | The model ignores the `response_format` or outputs markdown-fenced JSON with syntax errors. | The `summarizer.py` catches the JSON parse error, and retries the LLM call up to 2 times with a stricter system prompt. |
| **Token Budget Exceeded** | 500 extremely long reviews cause the prompt to exceed the context window. | The summarizer truncates the input by sampling a maximum of `N` (e.g., 20) representative reviews per cluster before building the prompt. |
| **PII scrubber misses local formats** | An obscure regional phone number format slips past the regex. | The agent relies on a defense-in-depth approach: Play Store scraper pseudonymizes author names first. The LLM is instructed to treat reviews as data. Residual risk remains low as reviews are public anyway. |

---

## 3. Delivery (Docs & Gmail MCP)

| Scenario | System Behavior | Mitigation |
|---|---|---|
| **Concurrent runs** | Two schedulers trigger at the same time for the same week. | SQLite uses `IMMEDIATE` transactions. Only one process will successfully insert the `status="success"` row. The second will abort during the idempotency check. |
| **Partial Doc Append** | Network drops halfway through `batchUpdate`. Heading is appended, but table is missing. | Google Docs `batchUpdate` is atomic. It either completely succeeds or completely fails. |
| **Doc Success, Email Failure** | Section appended to Google Doc, but Gmail MCP fails to draft the email. | Orchestrator catches the email error, writes a `RunRecord` with `status="partial"`. Running again with `--force` detects the doc anchor exists, skips doc append, and retries the email draft. |
| **Google Doc becomes too large** | After 3 years, the Doc has 150+ sections and becomes slow to load. | **Future enhancement**: Implement an annual rotation (e.g., *Weekly Review Pulse — Groww 2026*). Update the `config.json` target Doc ID yearly. |

---

## 4. Edge Cases in CLI & Orchestration

| Scenario | System Behavior | Mitigation |
|---|---|---|
| **Week 53 / Leap Years** | ISO week edge cases around New Year. | The CLI uses Python's strict `datetime.date.fromisocalendar()` to ensure week math is always standard. |
| **Backfill overlapping with current run** | A user runs `--backfill` for the last 5 weeks while the cron job is running for the current week. | Idempotency locks rely on `(product, iso_week)`. The backfill and current run operate on different ISO weeks, so they won't collide. |
| **Stale "failed" state in SQLite** | A previous run crashed hard (OOM) leaving a `status="failed"`. | Idempotency only skips if `status="success"`. A `failed` run will automatically be retried on the next execution attempt. |
| **Missing Google Workspace permissions** | The Google account authenticating the MCP servers loses access to the target Doc. | The Docs MCP returns a 403 Forbidden. The orchestrator catches it, logs the error, and marks the run as `failed`. |
