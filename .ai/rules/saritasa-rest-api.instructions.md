# REST API Guidelines (Saritasa)

Follow these API design standards for generating or reviewing endpoints.

## 1. General & HTTP Verbs
- **Format**: JSON (`application/json`). Use **lowerCamelCase** for fields (`userName`).
- **Security**: SHA-256 (or better) with salt for passwords.
- `GET`: Retrieve data. No state changes. Cachable.
- `POST`: Create entity / perform action.
- `PUT`: Update entity. ID belongs in URL.
- `DELETE`: Delete entity. ID belongs in URL.

## 2. Response Codes
- `200` OK
- `400` Bad Request (Validation/business logic errors)
- `401` Unauthorized (Not authenticated)
- `403` Forbidden (Authenticated, lacks permission)
- `404` Not Found
- `500` Server Error

## 3. Success Responses
**Single Entity:**
```json
{ "id": 10, "firstName": "Ivan" }
```

**Lists (Must support filtering/pagination/sorting):**
Params: `offset`, `limit`, `page`, `pageSize`, `orderBy` (`name:asc`).

*Offset pagination:*
```json
{
  "metadata": { "offset": 100, "limit": 2, "totalCount": 2054 },
  "items": [ { "id": 654, "name": "test 1" } ]
}
```

*Page pagination:*
```json
{
  "metadata": { "page": 4, "totalPages": 4, "totalCount": 18, "pageSize": 5, "isFirstPage": false, "isLastPage": true },
  "items": [ ]
}
```

## 4. Error Responses
All errors must follow this structure. `debug` must be `null`/omitted in production.
```json
{
  "type": "Validation",
  "code": "10",
  "title": "There are validation errors in your request.",
  "status": 400,
  "errors": [
    { "field": "address.city", "messages": ["The field is required."] }
  ],
  "debug": { "stacktrace": "..." }
}
```

## 5. Authentication (JWT)
Endpoints:
- `POST /api/auth` (Login, returns `token` and `expiresIn`)
- `PUT /api/auth` (Refresh)
- `GET /api/auth` (Get current user)
- `DELETE /api/auth` (Logout)
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`

**Rules:**
- Send JWT in `Authorization` header.
- Default lifetime: 2 hours. Refresh window: 2 weeks.
- Forgot Password: Always return `200 OK` to prevent enumeration.
- Reset Password: Needs `email`, `token`, `newPassword` in body.

## 6. Health Checks
Provide two endpoints:
- `GET /liveness`: Kubernetes probe. Checks if process is alive (no external dependencies).
- `GET /health`: Full system check for monitoring. Status code dictates health (`200` OK, `500` Error, `503` Dependency down). JSON is informational.

*Response:*
```json
{
  "status": "Healthy",
  "results": [
    { "name": "ping", "status": "Healthy", "description": null }
  ]
}
```