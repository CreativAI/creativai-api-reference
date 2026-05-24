# Integration Guidelines

## Versioning

- Default to `/api/v2` unless a feature is explicitly documented under `/api/v3`
- Pin client behavior to documented response fields, not inferred internals
- Track backend release notes and update this reference folder in lockstep

## Idempotency And Safety

- Treat create/delete/update operations as stateful and potentially non-idempotent
- Use client-side safeguards for destructive endpoints (delete, cancel, remove)
- Store returned identifiers (`job_id`, `indexing_id`, `session_id`) durably

## Robust Client Behavior

- Use request timeouts for every call
- Retry transient failures with exponential backoff and jitter
- Implement circuit-breaker behavior for repeated dependency errors
- Add structured logs with request ids and endpoint names

## SSE And Long-Lived Connections

- For agentic chat SSE, handle reconnect with resume/session context
- Surface partial progress events in UI
- Use explicit user cancellation controls

## Live Stream UX Recommendations

- Distinguish states: waiting, ready, streaming, paused, stopped
- Poll readiness endpoints before declaring stream failure
- Display protocol-specific publish/playback URLs clearly
- Reconcile session state after reconnect or app restart

## Data Governance

- Do not log API keys, full tokens, or raw PII in client logs
- Redact sensitive fields before telemetry export
- Follow your organization retention policy for exported CSV and analytics artifacts
