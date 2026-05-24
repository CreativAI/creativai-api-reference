# Errors And Retries

## Response Shape

Most endpoints follow a success/error envelope.

Logical contract:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "string",
    "message": "human readable",
    "details": {},
    "timestamp": "ISO-8601"
  }
}
```

## Common HTTP Codes

- `400`: validation or request format issue
- `401`: missing or invalid authentication
- `403`: permission denied
- `404`: resource not found
- `409`: conflict (state transition or duplicate condition)
- `422`: semantic validation failure
- `429`: rate/usage limit hit
- `500`: unexpected server failure
- `503`: dependency/service temporarily unavailable

## Retry Guidance

Retryable in most clients:

- `429`
- `500`
- `502`
- `503`
- `504`

Do not retry blindly:

- `400`
- `401`
- `403`
- `404`
- `422`

## Backoff Strategy

Use exponential backoff with jitter.

Example sequence in seconds:

`1, 2, 4, 8, 16` with random jitter up to 30%.

## Observability Tips

- Attach a client request id per call
- Record endpoint, payload hash, status code, and latency
- Persist job ids for async workflows
