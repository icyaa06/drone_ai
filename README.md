# Drone AI Challenge Kazakhstan 2026

Full-stack participant portal built with Flask, SQLAlchemy, PostgreSQL, and a dependency-free responsive frontend.

## Included

- Participant-focused landing page with missions, stages, eligibility, deliverables, judging, and FAQ
- Six-step team application with client/server validation and file uploads
- PostgreSQL models for applications, team members, and uploaded documents
- Private status lookup using tracking code + team lead email
- Protected organizer dashboard with search, filters, detail review, document download, notes, and status updates
- Health endpoint and environment-based secrets

## Run in Visual Studio / terminal

1. Activate the environment:

   `venv\Scripts\activate`

2. Install dependencies if needed:

   `pip install -r requirements.txt`

3. Copy `.env.example` to `.env` and fill in `DATABASE_URI`, `SECRET_KEY`, and `ADMIN_PASSWORD`.

4. Ensure PostgreSQL is running and the configured database exists.

5. Start:

   `python app.py`

6. Open `http://127.0.0.1:5000`.

Tables are created automatically on first start. Uploaded files are stored under `uploads/`; metadata stays in PostgreSQL.

## Production notes

- Change the admin password and secret key before publishing.
- Serve behind HTTPS and a production WSGI server.
- Put uploaded files in managed object storage for multi-server deployment.
- Back up PostgreSQL and the upload directory together.

## Deploy option: Render / Railway / similar Python host

1. Push this folder to a private GitHub repository.

2. Create a PostgreSQL database on the hosting platform.

3. Create a Web Service from the repository.

4. Set environment variables in the hosting dashboard:

   - `DATABASE_URI=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DBNAME`
   - `SECRET_KEY=` a long random value
   - `ADMIN_PASSWORD=` a new strong admin password
   - `FLASK_DEBUG=false`
   - `MAX_CONTENT_LENGTH_MB=25`

5. Use these commands:

   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`

6. Open `/api/health` on the deployed URL. It should return `"database":"connected"`.

Important: this app currently stores uploaded participant documents in the local `uploads/` folder. That is fine for local use and simple single-server hosting, but for production with redeploys or multiple servers, move uploads to object storage such as S3, Cloudflare R2, or Supabase Storage.

## Deploy option: VPS

1. Install Python 3.11+, PostgreSQL, and Nginx.
2. Clone the project to the server and create `.env`.
3. Install dependencies with `pip install -r requirements.txt`.
4. Run with Gunicorn: `gunicorn app:app --bind 127.0.0.1:8000`.
5. Put Nginx in front of Gunicorn, enable HTTPS with Certbot, and proxy traffic to `127.0.0.1:8000`.
6. Add a process manager such as systemd so the app restarts automatically.
