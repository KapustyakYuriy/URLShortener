# URLShortener

URL shortener with click analytics. Two services — Django REST API and async Python worker — communicate via Redis Pub/Sub. PostgreSQL stores users, URLs, and enriched click events. All orchestrated with Docker Compose.


## Project architecture
```
URLShortener/
│
├── api/
│	├── apps/
│	│	├── accounts/
│	│	│	├── serializers.py
│	│	│	├── tests.py
│	│	│	├── urls.py
│	│	│	└── views.py
│	│	├── analytics/
│	│	│	├── apps.py
│	│	│	├── models.py
│	│	│	├── subscriber.py
│	│	│	├── views.py
│	│	│	└── tests.py
│	│	└── urls/
│	│		├── models.py
│	│		├── serializers.py
│	│		├── tests.py
│	│		├── urls.py
│	│		├── utils.py
│	│		└── views.py
│	├── config/
│	│		├── logging_setup.py
│	│		├── settings.py
│	│		└── urls.py
│	├── conftest.py
│	├── manage.py
│	├── pytest.ini
│	├── requirements.txt
│	└── Dockerfile
│
├── worker/
│	├── app/
│	│	├── config.py
│	│	├── logging_setup.py
│	│	├── main.py
│	│	└── redis_client.py
│	├── tests/
│	│	└── test_main.py
│	├── pytest.ini
│	├── requirements.txt
│	└── Dockerfile
│
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## Setup
Requirements: Docker, Docker Compose
```
git clone <repo-url>
cd URLShortener
cp .env.example .env
docker compose up
```
API available at http://localhost:8000. Migrations run automatically on startup.

### Run tests
```
docker compose run --rm api pytest
```

## Environment variables
| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Required |
| `DJANGO_DEBUG` | `False` | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `ENABLE_DEBUG_TOOLBAR` | `0` | Enable debug toolbar (requires DEBUG=True) |
| `POSTGRES_DB` | `urlshortener` | Database name |
| `POSTGRES_USER` | `urlshortener` | Database user |
| `POSTGRES_PASSWORD` | `urlshortener` | Database password |
| `POSTGRES_HOST` | `postgres` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `CLICKS_RAW_CHANNEL` | `clicks:raw` | Raw click events channel |
| `CLICKS_ENRICHED_CHANNEL` | `clicks:enriched` | Enriched click events channel |
| `LOG_LEVEL` | `INFO` | Log level for both services |

## API
All URL and analytics endpoints require Authorization: Bearer <access_token>.

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | No | Create user, returns tokens |
| POST | `/api/auth/login/` | No | Returns tokens |
| POST | `/api/auth/refresh/` | No | Exchange refresh token for new access token |

**Register:**

Request:
```json
{ "username": "user", "password": "strongpass123" }
```

Response:
```json
{ "access": "<token>", "refresh": "<token>", "message": "user created successfully" }
```

**Login:**

Request:
```json
{ "username": "user", "password": "strongpass123" }
```

Response:
```json
{ "access": "<token>", "refresh": "<token>" }
```

**Refresh:**

Request:
```json
{ "refresh": "<refresh_token>" }
```

Response:
```json
{ "access": "<new_token>", "refresh": "<new_refresh_token>" }
```

### URLs

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/urls/` | Yes | Create short URL |
| GET | `/api/urls/` | Yes | List user's URLs with click counts (paginated) |
| GET | `/api/urls/{id}/` | Yes | Retrieve URL with last 10 clicks |
| DELETE | `/api/urls/{id}/` | Yes | Delete URL (owner only, returns 404 for non-owner) |
| GET | `/<short_code>/` | No | Redirect 302 to original URL |

**Create short URL:**

Request:
```json
{ "original_url": "https://example.com" }
```

Response:
```json
{
	"id": 1,
	"original_url": "https://example.com",
	"short_code": "aB3xY7z",
	"created_at": "2026-06-01T12:00:00Z",
	"click_count": 0
}
```

**List URLs:**

Response:
```json
{
	"count": 1,
	"next": null,
	"previous": null,
	"results": [
		{
			"id": 1,
			"original_url": "https://example.com",
			"short_code": "aB3xY7z",
			"created_at": "2026-06-01T12:00:00Z",
			"click_count": 42
		}
	]
}
```

**Retrieve with recent clicks:**

Response:
```json
{
	"id": 1,
	"original_url": "https://example.com",
	"short_code": "aB3xY7z",
	"created_at": "2026-06-01T12:00:00Z",
	"click_count": 42,
	"recent_clicks": [
		{
			"clicked_at": "2026-06-09T10:00:00Z",
			"ip_address": "1.2.3.4",
			"browser": "Chrome",
			"os": "Windows",
			"device_type": "desktop"
		}
	]
}
```

### Analytics

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/urls/{id}/stats/` | Yes | Stats for one URL |
| GET | `/api/stats/summary/` | Yes | Stats across all user's URLs |

**Stats:**

Response:
```json
{
	"total_clicks": 42,
	"clicks_per_day": [
		{ "date": "2026-05-11", "count": 0 },
		{ "date": "2026-05-12", "count": 3 }
	],
	"top_browsers": [{ "browser": "Chrome", "count": 30 }],
	"top_os": [{ "os": "Windows", "count": 25 }]
}
```

clicks_per_day always contains exactly 30 entries including days with zero clicks.

**Summary:**

Response:
```json
{
	"total_urls": 5,
	"total_clicks": 200,
	"top_urls": [
		{ "id": 1, "short_code": "aB3xY7z", "original_url": "https://example.com", "click_count": 42 }
	]
}
```

## Flow
```
GET /<short_code>
→ api: redirect 302, publish to clicks:raw

worker: subscribe clicks:raw
→ parse user-agent (browser, os, device_type)
→ publish to clicks:enriched

api background thread: subscribe clicks:enriched
→ write ClickEvent to PostgreSQL
```

## Redis message format
`clicks:raw`:
```json
{
	"short_code": "aB3xY7z",
	"ip_address": "1.2.3.4",
	"user_agent": "Mozilla/5.0 ...",
	"clicked_at": "2026-06-01T12:00:00+00:00"
}
```
`clicks:enriched`:
```json
{
	"short_code": "aB3xY7z",
	"ip_address": "1.2.3.4",
	"user_agent": "Mozilla/5.0 ...",
	"clicked_at": "2026-06-01T12:00:00+00:00",
	"browser": "Chrome",
	"os": "Windows",
	"device_type": "desktop"
}
```

## Query counts

| Endpoint | Queries | Notes |
|---|---|---|
| `POST /api/auth/register/` | 2 | |
| `POST /api/auth/login/` | 2 | |
| `POST /api/auth/refresh/` | 13 | JWT blacklisting + token rotation |
| `POST /api/urls/` | 2 | |
| `GET /api/urls/` | 2 | `annotate(click_count=Count("clickevent"))` — constant regardless of URL count |
| `GET /api/urls/{id}/` | 3 | `prefetch_related` — constant regardless of click count |
| `DELETE /api/urls/{id}/` | 4 | |
| `GET /<short_code>/` | 1 | No auth required |
| `GET /api/urls/{id}/stats/` | 6 | |
| `GET /api/stats/summary/` | 3 | |

## Indexes

| Field | Type | Justification |
|---|---|---|
| `ShortURL.short_code` | Unique (auto B-tree) | Every redirect does a lookup by short_code — full table scan without index |
| `ClickEvent.clicked_at` | `db_index=True` | Time-range filter for 30-day stats aggregation |
| `ShortURL.owner` FK | Auto (Django) | Filters every authenticated endpoint by owner |
| `ClickEvent.short_url` FK | Auto (Django) | Filters every analytics query by URL |

## Short_code generation
Random 7-character string from [a-zA-Z0-9] (base62). Uniqueness checked before saving with a retry loop. Random generation was chosen over encoded ID — it requires no knowledge of the row ID before insert and reveals nothing about the total number of URLs.

## Separate Dockerfiles
api and worker have different dependencies, different entrypoints, and different startup logic (migrate + gunicorn vs python -m app.main). A shared base image would save build time but add coupling between two independent services.

## What I learned
- **DRF ModelViewSet and routers** — previously worked mostly with FastAPI, so generic ViewSets were new. One class replaces five separate views and the router handles URL generation automatically. `@action` adds custom endpoints without leaving the ViewSet pattern.
- **DRF serializers** — learned to move validation logic out of views into serializers. `ModelSerializer` generates fields from the model automatically, `validate_<field>` methods hook into `is_valid()`, and `create`/`update` handle persistence. Views become thin orchestrators.
- **Redis Pub/Sub** — fire-and-forget messaging between two independent services. The subscriber must be running when the message is published, otherwise it is lost. For this task that is acceptable; production systems would use Redis Streams for durability.
- **N+1 queries** — learned how `annotate` and `prefetch_related` replace per-row queries with a fixed number of SQL statements, and how to verify this with `CaptureQueriesContext` in tests.
- **Loguru setup** — configuring a single logger that intercepts Django's built-in logging and formats everything consistently across both services.
- **AppConfig.ready()** — how to start a background thread alongside Django, and why guards against management commands are necessary to avoid double-starting the subscriber.
- **JWT rotation and blacklisting** — `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` invalidate used refresh tokens automatically, which explains the higher query count on `/api/auth/refresh/`.
- **asyncio with redis.asyncio** — structuring an async event loop, using `create_task` for concurrent event handling without blocking the subscriber loop.