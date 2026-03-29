# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Initialize database (creates tables + seeds buildings/units/admin user)
FLASK_APP=app.py flask init-db

# Run development server
FLASK_APP=app.py flask run

# Create an additional board user interactively
FLASK_APP=app.py flask create-user
```

Default admin credentials after `init-db`: `admin` / `admin`

## Architecture

All application code lives in two files: `app.py` (Flask app factory + all routes) and `models.py` (SQLAlchemy models). There are no separate route files or packages.

**Three Flask blueprints registered in `create_app()`:**
- `public` (prefix: `/`) — unauthenticated resident ticket submission form
- `auth` (prefix: `/board`) — login/logout only
- `board` (prefix: `/board`) — all board member views, protected by `@login_required`

**Data model relationships:**
- `Building` → `Unit` (one-to-many) → `Resident` (one-to-many)
- `Ticket` links to both `Unit` and `Building` directly; `unit_id` takes precedence and `building_id` is derived from it when a unit is selected. `Ticket.effective_building` property handles this logic.
- `Ticket` ↔ `Vendor` is many-to-many via the `TicketVendor` join model (not a SQLAlchemy `secondary` table — it's an explicit model).
- `Attachment` stores files with `file_type` of `"photo"` or `"document"`. Physical files are saved to `static/uploads/photos/` or `static/uploads/documents/` using UUID-based filenames.
- `BoardUser` uses `flask_login.UserMixin`; password hashed with Werkzeug.

**Ticket status flow:** New → Assigned → Waiting → Completed
Status transitions auto-set `date_assigned` and `date_completed` timestamps in the ticket detail POST handler.

**Constants in `models.py`** (used throughout templates and routes):
- `STATUS_CHOICES`, `CATEGORY_CHOICES`, `PRIORITY_CHOICES`

**`seed.py`** contains `UNIT_BUILDING_MAP` and `BUILDING_NAMES` — edit these to change the community layout. Called by `flask init-db`, safe to re-run (checks for existence before inserting).

**`import_residents.py`** — standalone script for bulk-importing residents (separate from the main app flow).
