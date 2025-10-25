# Riichi Tracker (Django + Poetry + Docker)

Base scaffold for a Riichi Mahjong games tracker using Django, managed with Poetry, and containerized with Docker + Compose.

## Quick Start (Docker Compose)

- Copy env: `cp .env.example .env`
- Build and run: `docker compose up --build`
- App: http://localhost:8000/ (healthcheck at `/health/`)

## Local Dev (Poetry)

- Install Poetry (if not installed): https://python-poetry.org/docs/#installation
- Create env and install deps:
  - `poetry install`
- Create `.env`: `cp .env.example .env`
- Run migrations: `poetry run python manage.py migrate`
- Start server: `poetry run python manage.py runserver`

## Environment

- `DJANGO_DEBUG`: `True|False` (default `True`)
- `DJANGO_SECRET_KEY`: app secret (change in production)
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames/IPs

## Notes

- Uses SQLite by default; DB stored at `db.sqlite3` in the repo root.
- Docker image installs Poetry and only the main deps; dev tools remain for local use.

### Uploads / Media

- User uploads (avatars) are stored under `MEDIA_ROOT` (`/app/media`) and served at `MEDIA_URL` (`/media/`).
- In production, Nginx serves `/media/` directly from `/app/media` (see `docker-compose.prod.yml`). The `media` folder is volume-mounted: `./media:/app/media` so uploads persist across deploys.
- For higher traffic or multiple instances, move media to object storage (e.g., S3 via `django-storages`) or serve `/media/` through a dedicated web server.

## Deployment

This repo includes a GitHub Actions workflow to build a Docker image and deploy it to a DigitalOcean droplet over SSH.

Prerequisites:

- Droplet with Docker and Docker Compose plugin installed (`docker --version` and `docker compose version`).
- A non-root SSH user with access to Docker (in the `docker` group), or root.
- A production `.env` on the droplet at `~/apps/riichi-tracker/.env` with at least:
  - `DJANGO_SECRET_KEY=...`
  - `DJANGO_DEBUG=False`
  - `DJANGO_ALLOWED_HOSTS=your.domain,IP`
  - Optionally `DJANGO_CSRF_TRUSTED_ORIGINS=https://your.domain`

GitHub repository secrets (Settings → Secrets and variables → Actions → New repository secret):

- `DROPLET_HOST`: droplet IP or hostname
- `DROPLET_USER`: SSH username
- `SSH_PRIVATE_KEY`: private key contents for the above user (PEM, no passphrase)
- `DROPLET_PORT` (optional): SSH port, defaults to `22`

How it works:

- On push to `main`, the workflow builds the Docker image from this repo.
- It saves and uploads the image to the droplet over SSH (no registry needed).
- It runs Django migrations in a one-off container, then restarts the app container.
- SQLite is persisted by binding `~/apps/riichi-tracker/db/db.sqlite3` to `/app/db/db.sqlite3` inside the container.

### Production stack (Nginx + Gunicorn)

- `docker-compose.prod.yml` runs Django via Gunicorn (`web`) and fronts it with Nginx (`nginx`).
- Nginx serves `/static/` from `/app/staticfiles` and `/media/` from `/app/media`, and proxies app routes to `web:8000`.
- Volumes:
  - `./staticfiles:/app/staticfiles` (collectstatic output)
  - `./media:/app/media` (user uploads)

Start or update prod:

```
docker compose -f docker-compose.prod.yml up -d --build
```

Check:

- App: http://localhost:8000/
- Example static: http://localhost:8000/static/admin/css/base.css
- Example media: http://localhost:8000/media/avatars/<uploaded-file>

If you need TLS or a public hostname, put Nginx behind a reverse proxy or terminate TLS directly in Nginx.

First-time droplet setup (example):

```
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER  # then log out/in

mkdir -p ~/apps/riichi-tracker/db
cp .env.example ~/apps/riichi-tracker/.env  # then edit it for production
```

Once secrets are set, push to `main` to trigger deployment.

### Translations
 ./dev django-admin makemessages -l uk
./dev django-admin compilemessages

