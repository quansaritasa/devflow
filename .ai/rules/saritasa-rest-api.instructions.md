# REST API Guidelines (Saritasa)

These instructions define REST API design and response format standards to follow when generating, reviewing, or suggesting API-related code.

---

## 1. General

- Use **lowerCamelCase** for all JSON field names (e.g., `userName` not `UserName`).
- Always send and receive data in **JSON format** (`application/json`).
- Use **SHA-256 or better with salt** for password hashing. Never store or transmit plain-text passwords.

---

## 2. HTTP Verbs

| Verb     | Usage |
|----------|-------|
| `GET`    | Retrieve a single entity or a list. Must NOT modify state. Results can be cached. |
| `POST`   | Create an entity or perform an action. |
| `PUT`    | Update an entity. The entity ID is typically provided in the URL. |
| `DELETE` | Delete an entity. The entity ID is typically provided in the URL. |

---

## 3. HTTP Response Codes

| Code | Meaning |
|------|---------|
| `200` | OK — request succeeded. |
| `400` | Bad Request — validation errors or exceptional business logic case. |
| `401` | Unauthorized — user is not authenticated. |
| `403` | Forbidden — user is authenticated but lacks permission. |
| `404` | Not Found — entity requested by ID does not exist. |
| `500` | Server Error — unhandled exception, database failure, etc. |

---

## 4. Success Responses

### Single Entity (`GET /api/customer/{id}`)

```json
HTTP/1.1 200
Content-Type: application/json
{
  "id": 10,
  "firstName": "Ivan",
  "lastName": "Nguyen"
}
```

### List of Entities

List endpoints must support **filtering**, **pagination**, and **sorting** via query string parameters:

| Parameter  | Description |
|------------|-------------|
| `offset`   | Number of records to skip. Default: `0`. Use with `limit`. |
| `limit`    | Max records to return. Backend defines default. Use with `offset`. |
| `page`     | Page number. Default: `1`. Use with `pageSize`. |
| `pageSize` | Records per page. Backend defines default. Use with `page`. |
| `orderBy`  | Sorting columns with direction. Format: `name:asc,duration:desc`. Default direction is `asc`. |

**Offset-based pagination response:**
```json
{
  "metadata": {
    "offset": 100,
    "limit": 2,
    "totalCount": 2054
  },
  "items": [
    { "id": 654, "name": "test 1" },
    { "id": 655, "name": "test 2" }
  ]
}
```

**Page-based pagination response:**
```json
{
  "metadata": {
    "page": 4,
    "totalPages": 4,
    "totalCount": 18,
    "pageSize": 5,
    "isFirstPage": false,
    "isLastPage": true
  },
  "items": [ ... ]
}
```

---

## 5. Error Responses

All error responses must follow this structure:

```json
{
  "type": "Validation",
  "code": "10",
  "title": "There are validation errors in your request.",
  "status": 400,
  "errors": [
    {
      "field": "userName",
      "messages": ["User with such username already exists."]
    },
    {
      "field": "address.city",
      "messages": ["The field is required."]
    }
  ],
  "debug": {
    "stacktrace": "ValidationException: ..."
  }
}
```

### Field Definitions

- `type` — Error type name (e.g., exception class name).
- `code` — Backend error/exception code for client-side grouping and parsing.
- `title` — Human-readable message that can be shown to the user.
- `errors` — Array of per-field validation errors (optional).
  - `field` — Field name (use dot notation for nested fields, e.g., `address.city`).
  - `messages` — List of error strings for that field.
- `debug` — Developer-facing debug info (stack trace, etc.). **Must be `null` or omitted in production.**

### Standard Error Examples

**401 Unauthorized:**
```json
{
  "type": "AuthorizationRequired",
  "code": 3,
  "title": "Authorization required.",
  "status": 401
}
```

**500 Server Error:**
```json
{
  "type": "ServerError",
  "code": 10,
  "title": "Server error. Please try again later.",
  "status": 500
}
```

---

## 6. Authentication

Use JWT-based authentication.

### Endpoints

| Method   | URL                      | Description |
|----------|--------------------------|-------------|
| `POST`   | `/api/auth`              | Authenticate and receive a token. |
| `PUT`    | `/api/auth`              | Refresh an existing token. |
| `GET`    | `/api/auth`              | Get current logged-in user info. |
| `DELETE` | `/api/auth`              | Logout / invalidate the current token. |
| `POST`   | `/api/auth/forgot-password` | Initiate forgot password flow. |
| `POST`   | `/api/auth/reset-password`  | Complete password reset. |

### Token Usage

- The JWT token must be sent in the `Authorization` header:
- Authentication response must include `token` and `expiresIn` fields.
- Default token lifetime: **2 hours**.
- Default token refresh window: **2 weeks**.

### Forgot Password

- Always return `200 OK` regardless of whether the email is registered (to prevent user enumeration).
- Send a password reset link via email.

### Password Reset

- Accept `email`, `token`, and `newPassword` in the request body.
- Return `200 OK` on success.

---

## 7. Health Check Endpoints

Implement two health check endpoints for every service:

| Endpoint    | Purpose |
|-------------|---------|
| `GET /liveness` | Kubernetes liveness probe. Must only check that the web server process is alive — no external dependencies. |
| `GET /health`   | Full system health check. Used for automated monitoring/alerting. |

### `/health` Response Structure

```json
{
  "status": "Healthy",
  "results": [
    {
      "name": "ping",
      "status": "Healthy",
      "description": null
    },
    {
      "name": "process_allocated_memory",
      "status": "Healthy",
      "description": "Allocated megabytes in memory: 3 mb"
    }
  ]
}
```

### Health Check Response Codes

| Code | Meaning |
|------|---------|
| `200` | All systems healthy. |
| `500` | Internal server error — not necessarily down, but must be investigated. |
| `503` | One or more dependent services are unavailable. |

The health checker must rely solely on the **HTTP response code**. The JSON payload is informational only.