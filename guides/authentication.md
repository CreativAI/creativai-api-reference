# Authentication

## API Keys

All authenticated endpoints accept your API key via one of two headers — both are equivalent:

```
X-API-Key: sk_live_xxxxxxxxxxxxxxxxxxxxx
Authorization: Bearer sk_live_xxxxxxxxxxxxxxxxxxxxx
```

### Verify Your Key

```bash
# No auth required — use to test key validity
curl "$CREATIVAI_BASE_URL/api/v2/users/api-key-check" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

Response:
```json
{"success": true, "data": {"valid": true}}
```

### Get Current User

```bash
curl "$CREATIVAI_BASE_URL/api/v2/users/me" \
  -H "X-API-Key: $CREATIVAI_API_KEY"
```

## Response Envelope

Every response (success or error) uses the same envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

On error:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key",
    "details": {},
    "timestamp": "2026-05-25T10:00:00Z"
  }
}
```

## HTTP Status Codes

| Status | Error Code | Meaning |
|---|---|---|
| 200 | — | Success |
| 201 | — | Created |
| 202 | — | Accepted (async job started) |
| 207 | `PARTIAL_SUCCESS` | Some operations succeeded, some failed |
| 400 | `BAD_REQUEST` | Invalid request body or parameters |
| 401 | `UNAUTHORIZED` | Missing or invalid API key |
| 403 | `FORBIDDEN` | Valid key, insufficient permissions |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Resource already exists |
| 422 | `UNPROCESSABLE_ENTITY` | Validation error (missing required field, wrong type) |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected server failure |
| `TIER_LIMIT` | — | Plan quota exceeded |
| `INSUFFICIENT_CREDITS` | — | Out of AI credits |

## Roles & Authorization

Collection-level operations have a three-tier access system:

| Role | Capabilities |
|---|---|
| `admin` | Full control: invite, remove members, change roles, delete collection, create tasks |
| `read_write` | Upload, index, search, create plates, run KE, manage tasks you created |
| `read_only` | Read collection data, search, view plates; cannot modify anything |
| `viewer` | Legacy alias for `read_only` |

**Rule of thumb**: Use `ensure_admin_access_on_collection` for destructive operations. All other mutations require `read_write` or higher.

## WebRTC Authentication (WHIP/WHEP)

WebRTC signaling endpoints don't support custom request headers (browser limitation). Pass the API key as a query parameter:

```
POST /api/v2/live-stream/sessions/{session_id}/whip?token=YOUR_API_KEY
```

## Security Best Practices

- Never embed API keys in frontend source code or mobile app bundles
- Store keys in environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Use separate keys per environment (dev / staging / production)
- Rotate keys regularly; revoke compromised keys immediately
- All communication must use HTTPS — HTTP is not supported
