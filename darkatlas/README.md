# DarkAtlas — Asset Management API

A backend module for the **DarkAtlas Attack Surface Monitoring** platform.  
Tracks domains, subdomains, IPs, services, certificates, and technologies — with full lifecycle management and relationship graphing.

---

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env          # edit API_KEY at minimum

# 2. Start everything
docker-compose up --build

# 3. API is live at http://localhost:8000
# 4. Interactive docs at http://localhost:8000/docs
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://darkatlas:darkatlas@db:5432/darkatlas` | PostgreSQL connection string |
| `API_KEY` | `changeme-secret-api-key` | API key for write operations |
| `DEBUG` | `false` | Enable debug mode |

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

Tests use **SQLite in-memory** — no PostgreSQL required for testing.

---

## API Overview

All write endpoints require the header: `X-API-Key: <your-key>`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/assets/` | Create an asset |
| `GET` | `/api/v1/assets/` | List assets (filter, sort, paginate) |
| `GET` | `/api/v1/assets/{id}` | Get a single asset |
| `GET` | `/api/v1/assets/{id}/graph` | Get asset + all related assets |
| `PATCH` | `/api/v1/assets/{id}` | Update asset (status, tags, metadata) |
| `POST` | `/api/v1/assets/{id}/stale` | Mark asset as stale |
| `DELETE` | `/api/v1/assets/{id}` | Delete asset |
| `POST` | `/api/v1/import/` | Bulk import with deduplication |
| `POST` | `/api/v1/relationships/` | Create a relationship |
| `GET` | `/api/v1/relationships/` | List all relationships |
| `DELETE` | `/api/v1/relationships/{id}` | Delete a relationship |
| `GET` | `/health` | Health check |

Full OpenAPI docs auto-generated at `/docs`.

### Filtering & Pagination

```
GET /api/v1/assets/?type=subdomain&status=active&tag=prod&value_contains=api&page=1&page_size=20&sort_by=last_seen&sort_dir=desc
```

---

## Design Decisions & Assumptions

### Deduplication
- **Dedup key:** `(type, value)` — two assets are the same if they share type and value regardless of source.
- On re-import: `last_seen` is updated, tags are merged (union), metadata is merged (incoming wins on conflict).
- A **stale** asset that reappears automatically returns to **active**.

### Relationships
- Stored as a directed graph: `(from_id, to_id, relation_type)`.
- Built-in types: `subdomain_of`, `covers`, `resolves_to`, `runs_on` — but the field is free-form.
- Cascade delete: removing an asset removes all its relationships.

### Authentication
- Simple API key via `X-API-Key` header on all write operations (POST, PATCH, DELETE).
- Read operations (GET) are public to allow monitoring dashboards without auth.

### Error Handling
- Bulk import is **fault-tolerant**: a bad record fails gracefully and is counted in `failed`; the rest of the batch proceeds.
- All errors return structured JSON: `{"detail": "..."}`.

### Lifecycle
- `first_seen`: set once on creation, never updated.
- `last_seen`: updated on every re-sighting or update.
- `status`: `active` → `stale` → `archived` (or back to `active` on re-sighting).

### What I Would Add Next
- Alembic migrations for production schema management
- Multi-tenant scoping (organization_id on every asset)
- Role-based access control (read-only vs admin API keys)
- CI pipeline with GitHub Actions
- Rate limiting and caching on list endpoints
- Certificate expiry warnings endpoint
