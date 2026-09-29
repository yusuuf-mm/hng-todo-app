# AGENTS.md — hng-todo-app

## Project overview

Simple to-do web app for an internship task. Add, complete, edit, delete tasks.
Filter: all / active / completed. Server-rendered, no JS framework.
Develop and test locally first; final goal is deploying to Vercel (demo-grade persistence).

## Tech stack

- Python 3.12+ (dev on 3.14), Flask 3.x, Jinja templates, plain CSS
- SQLite via stdlib `sqlite3` only — all DB code lives in `db.py`
- Forms: Flask-WTF (WTForms + CSRF protection)
- Env config: python-dotenv (`.env` local, never committed)
- Packages managed with `uv`. `pyproject.toml` + `uv.lock` are source of truth.
  Vercel uses `requirements.txt`, which is exported from uv (see commands).
- Dev tools: pytest, ruff

## File structure

```
hng-todo-app/
  pyproject.toml      # uv deps (flask, flask-wtf, python-dotenv; dev: pytest, ruff)
  uv.lock             # locked by uv, do not hand-edit
  requirements.txt    # exported for Vercel ONLY — regen on dep change, do not add manually
  .python-version     # pinned python for uv (3.14, supported by Vercel)
  .env.example        # SECRET_KEY=, TODO_DB_PATH= (copy to .env locally)
  .gitignore          # venv, __pycache__, *.db, .env, .vercel/
  app.py              # Flask app, routes, exposes `app`, calls init_db() on startup
  db.py               # ONLY sqlite3 code: path, connect, init, CRUD + counts
  forms.py            # AddTaskForm, EditTaskForm (Flask-WTF)
  README.md           # user-facing readme, screenshot at public/UI.png
  public/             # static assets for README (UI screenshot)
  templates/
    base.html         # head, flash block, header/footer shell
    index.html        # add form + filter tabs + task list
    edit.html         # edit form
  static/style.css    # plain CSS, responsive, no frameworks
  tests/
    test_db.py        # db CRUD + filter + counts
    test_routes.py    # HTTP: add/toggle/edit/delete/filter/validation
```

## Run / test / deploy commands (uv)

```bash
# first setup
cp .env.example .env        # Windows: copy .env.example .env
uv sync                     # create .venv + install from lock
uv add flask flask-wtf python-dotenv            # runtime dep
uv add --dev pytest ruff                        # dev deps

# daily dev
uv run python app.py        # local server http://127.0.0.1:5000
uv run pytest -q            # tests
uv run ruff check .         # lint
uv run ruff format --check .  # format check (optional)

# keep Vercel file in sync after any dep change
uv export --format requirements-txt --no-hashes > requirements.txt

# deploy
vercel --prod               # from repo root; set SECRET_KEY in Vercel env dashboard
```

Vercel entry: `app.py` must expose module-level `app`. No `vercel.json` needed —
Vercel zero-config Flask detection routes all traffic to it. (A `/(.*)` →
`/app.py` rewrite breaks routing: the app receives `/app.py` as the path and
Flask 404s. Do not re-add it.)

## DB contract (`db.py` — swap-safe)

- `get_db_path()`: `TODO_DB_PATH` env > `/tmp/todo.db` if `VERCEL` is set > `todo.db` (repo root, dev).
- `get_conn()`: `sqlite3.connect(path)`, `row_factory = sqlite3.Row`.
- `init_db()`: `CREATE TABLE IF NOT EXISTS tasks (...)`. Called once at app startup.
- `get_tasks(filter)`, `add_task(title)`, `toggle_task(id)`, `update_title(id, title)`, `delete_task(id)`, `get_task(id)`, `get_counts()`.
- Schema: `tasks(id INTEGER PK AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)`.
- Validation: strip title in routes/forms, reject empty, max 200 chars. Never build SQL with f-strings — always `?` placeholders.
- To swap to hosted DB later (Neon/Supabase/Turso): keep these function names/signatures, replace internals only. `app.py` must not import `sqlite3` directly.

## Coding conventions (beginner-readable)

- Comments on every non-obvious block. Small functions, explicit names.
- Routes: thin — parse form, call `db.py`, `flash()` + `redirect`. No SQL in `app.py`/`forms.py`.
- Forms in `forms.py` only: `StringField` + `DataRequired` + `Length(max=200)`, strip whitespace before save.
- Templates: Jinja only, `url_for` for links/actions, `{{ form.csrf_token }}` in every POST form.
- CSS: plain `static/style.css`, CSS variables, mobile-first, single column `max-width: 680px`. Animate only `transform` + `opacity`.
- Copy: plain verbs, specific empty-state text per filter. No emojis, no lorem/Acme, no "seamless/elevate/unleash".

## UI rules (minimalist-ui + high-end, adapted to vanilla CSS)

- Palette: canvas `#F7F6F3`, card `#FFFFFF`, border `1px #EAEAEA`, text `#111111`, muted `#787774`. Colour-coded status: blue accent `#1F6C9F` (primary buttons, header bar), amber `#956400/#FBF3DB` (active tasks + tab), green `#346538/#EDF3EC` (done tasks + tab).
- Radius `8-12px`, no gradients, no heavy shadows, no pill containers (pills only for tiny badges).
- System font stack (no webfont download, keeps it fast on Vercel).
- Required states: empty (per filter), form error under input, flash toast, `:active scale(0.98)`, visible `:focus-visible` ring, 44px tap targets.
- Responsive: stack to full width under 640px. No horizontal scroll.

## Do / don't

Do:
- Keep all SQL in `db.py`.
- Use `?` placeholders, `redirect(url_for(...))` after POST.
- Regen `requirements.txt` via `uv export` after dep changes.
- Test locally with `uv run pytest` before pushing.

Don't:
- Don't add JS frameworks, ORMs, or Tailwind — plain CSS + Jinja only.
- Don't write outside `/tmp` on Vercel (read-only FS elsewhere).
- Don't commit `.env`, `*.db`, `.venv/`, `__pycache__/`.
- Don't store per-user data — single shared list is intentional for this demo.

## Vercel gotchas

1. SQLite is ephemeral: `/tmp/todo.db` is per-instance and wiped on cold start/scale. Todos disappear — expected for this demo, documented in README/footer.
2. Must set `SECRET_KEY` in Vercel project env, or Flask-WTF CSRF fails (500 on POST).
3. `uv.lock` is ignored by Vercel Python builder — `requirements.txt` must exist and be current.
4. `init_db()` runs on import so cold starts self-create the table.
5. No migrations, no background jobs, no websockets on serverless. Keep it request/response.

## Task checklist

- [x] Plan approved (sqlite3 + Flask-WTF + pytest/ruff + uv)
- [ ] Scaffold: pyproject, uv.lock, requirements.txt, .gitignore, .env.example
- [ ] `db.py` done + covered by `tests/test_db.py`
- [ ] `forms.py` + `app.py` routes done
- [ ] Templates + CSS done, responsive + empty/error states
- [ ] `uv run pytest -q` green, `uv run ruff check .` green
- [ ] Manual local run: add/complete/edit/delete/filter/validation
- [ ] `vercel --prod` smoke test + SECRET_KEY set
