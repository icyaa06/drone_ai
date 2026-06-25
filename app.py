import json
import re
import secrets
import uuid
from collections import Counter
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, abort, jsonify, request, send_file, send_from_directory, session
from flask_cors import CORS
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.utils import secure_filename

from config import ADMIN_PASSWORD, ALLOWED_ORIGINS, MAX_CONTENT_LENGTH, SECRET_KEY, UPLOAD_FOLDER
from database import Base, engine, session_scope
from models import ApplicationUpload, ChallengeApplication, TeamMember


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "drone_frontend"
MISSIONS = {
    "wildfire": "Wildfire Detection - forest fire detection on 100+ km²",
    "agriculture": "Precision Agriculture - crop monitoring on 1000+ ha",
    "rescue": "Search & Rescue - search over 50+ km²",
    "medical": "Medical Delivery - essential cargo over 15+ km",
    "infrastructure": "Infrastructure Monitoring - critical infrastructure inspection",
}
REGIONS = [
    "Астана", "Алматы", "Шымкент", "Абайская область", "Акмолинская область",
    "Актюбинская область", "Алматинская область", "Атырауская область",
    "Восточно-Казахстанская область", "Жамбылская область", "Жетысуская область",
    "Западно-Казахстанская область", "Карагандинская область", "Костанайская область",
    "Кызылординская область", "Мангистауская область", "Павлодарская область",
    "Северо-Казахстанская область", "Туркестанская область", "Улытауская область",
]
STATUSES = {"submitted", "screening", "stage2", "regional_review", "finalist", "declined"}
EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024

app = Flask(__name__, static_folder=None)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)


def response(data=None, message=None, status=200):
    payload = {"success": status < 400}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def text(name, required=True, limit=None):
    value = str(request.form.get(name, "")).strip()
    if required and not value:
        raise ValueError(f"Поле «{name}» обязательно")
    if limit and len(value) > limit:
        raise ValueError(f"Поле «{name}» превышает допустимую длину")
    return value


def valid_email(value):
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value or ""))


def valid_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def admin_required(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return response(message="Требуется вход администратора", status=401)
        return handler(*args, **kwargs)
    return wrapped


def tracking_code():
    return f"DAC26-{secrets.token_hex(4).upper()}"


def save_upload(file, category, application, db):
    if not file or not file.filename:
        return None
    original = secure_filename(file.filename) or "document"
    extension = Path(original).suffix.lower()
    if extension not in EXTENSIONS:
        raise ValueError(f"Формат файла {original} не поддерживается")
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"Файл {original} превышает 10 МБ")
    stored = f"{application.tracking_code}-{uuid.uuid4().hex}{extension}"
    file.save(UPLOAD_FOLDER / stored)
    upload = ApplicationUpload(
        application=application,
        category=category,
        original_name=original,
        stored_name=stored,
        content_type=file.mimetype or "application/octet-stream",
        size_bytes=size,
    )
    db.add(upload)
    return upload


@app.errorhandler(413)
def too_large(_error):
    return response(message="Общий размер загружаемых файлов слишком большой", status=413)


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return response(message="Ресурс не найден", status=404)
    return send_from_directory(FRONTEND_DIR, "404.html"), 404


@app.get("/api/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(select(1))
        return response({"database": "connected"})
    except OperationalError:
        return response({"database": "unavailable"}, status=503)


@app.get("/api/public/config")
def public_config():
    return response({"missions": MISSIONS, "regions": REGIONS})


@app.post("/api/applications")
def create_application():
    saved_paths = []
    try:
        members = json.loads(request.form.get("members", "[]"))
        if not isinstance(members, list) or not 1 <= len(members) <= 4:
            raise ValueError("В команде должно быть от 2 до 5 участников, включая лидера")
        for member in members:
            if not all(str(member.get(field, "")).strip() for field in ("full_name", "institution", "specialization")):
                raise ValueError("Заполните обязательные данные каждого участника")
            if member.get("email") and not valid_email(member["email"]):
                raise ValueError("Проверьте email участника")

        leader_email = text("leader_email", limit=254).lower()
        if not valid_email(leader_email):
            raise ValueError("Проверьте email лидера команды")
        mission = text("mission", limit=64)
        if mission not in MISSIONS:
            raise ValueError("Выберите миссию из списка")
        video_url = text("video_url", limit=500)
        repository_url = text("repository_url", required=False, limit=500)
        if not valid_url(video_url) or not valid_url(repository_url):
            raise ValueError("Ссылки должны начинаться с http:// или https://")
        if request.form.get("consent_personal_data") != "true" or request.form.get("consent_rules") != "true" or request.form.get("originality_confirmed") != "true":
            raise ValueError("Подтвердите все обязательные согласия")

        with session_scope() as db:
            application = ChallengeApplication(
                tracking_code=tracking_code(),
                team_name=text("team_name", limit=50),
                region=text("region", limit=80),
                institution=text("institution", limit=180),
                leader_name=text("leader_name", limit=160),
                leader_specialization=text("leader_specialization", limit=180),
                leader_email=leader_email,
                leader_phone=text("leader_phone", limit=40),
                mission=mission,
                project_title=text("project_title", limit=180),
                idea_summary=text("idea_summary", limit=500),
                problem_statement=text("problem_statement", limit=4000),
                proposed_solution=text("proposed_solution", limit=4000),
                expected_result=text("expected_result", limit=3000),
                technologies=text("technologies", required=False, limit=1500),
                repository_url=repository_url or None,
                video_url=video_url,
                mentor_name=text("mentor_name", required=False, limit=160) or None,
                mentor_organization=text("mentor_organization", required=False, limit=180) or None,
                mentor_email=text("mentor_email", required=False, limit=254).lower() or None,
                consent_personal_data=True,
                consent_rules=True,
                originality_confirmed=True,
            )
            if application.mentor_email and not valid_email(application.mentor_email):
                raise ValueError("Проверьте email ментора")
            db.add(application)
            db.flush()
            for item in members:
                db.add(TeamMember(
                    application=application,
                    full_name=str(item["full_name"]).strip()[:160],
                    institution=str(item["institution"]).strip()[:180],
                    specialization=str(item["specialization"]).strip()[:180],
                    email=str(item.get("email", "")).strip().lower()[:254] or None,
                ))
            required_idea = request.files.get("idea_document")
            if not required_idea or not required_idea.filename:
                raise ValueError("Прикрепите описание идеи")
            for category, files in (
                ("idea_document", [required_idea]),
                ("student_document", request.files.getlist("student_documents")),
                ("additional", request.files.getlist("additional_files")),
            ):
                for file in files:
                    upload = save_upload(file, category, application, db)
                    if upload:
                        saved_paths.append(UPLOAD_FOLDER / upload.stored_name)
            if len(request.files.getlist("student_documents")) < 1:
                raise ValueError("Прикрепите подтверждение статуса студента")
            code = application.tracking_code
        return response({"tracking_code": code}, "Заявка успешно отправлена", 201)
    except (ValueError, json.JSONDecodeError) as error:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        return response(message=str(error), status=400)
    except IntegrityError:
        for path in saved_paths:
            path.unlink(missing_ok=True)
        return response(message="Не удалось создать уникальный номер заявки. Повторите отправку.", status=409)


@app.post("/api/applications/status")
def application_status():
    payload = request.get_json(silent=True) or {}
    code = str(payload.get("tracking_code", "")).strip().upper()
    email = str(payload.get("email", "")).strip().lower()
    with session_scope() as db:
        application = db.scalar(select(ChallengeApplication).where(
            ChallengeApplication.tracking_code == code,
            func.lower(ChallengeApplication.leader_email) == email,
        ))
        if not application:
            return response(message="Заявка с такими данными не найдена", status=404)
        return response(application.public_status())


@app.post("/api/admin/login")
def admin_login():
    payload = request.get_json(silent=True) or {}
    supplied = str(payload.get("password", ""))
    if not secrets.compare_digest(supplied, ADMIN_PASSWORD):
        return response(message="Неверный пароль", status=401)
    session.clear()
    session["is_admin"] = True
    return response(message="Вход выполнен")


@app.post("/api/admin/logout")
def admin_logout():
    session.clear()
    return response(message="Вы вышли из системы")


@app.get("/api/admin/me")
@admin_required
def admin_me():
    return response({"authenticated": True})


@app.get("/api/admin/stats")
@admin_required
def admin_stats():
    with session_scope() as db:
        applications = db.scalars(select(ChallengeApplication)).all()
        statuses = Counter(item.status for item in applications)
        missions = Counter(item.mission for item in applications)
        return response({
            "total": len(applications),
            "today": sum(1 for item in applications if item.submitted_at.date() == datetime.now(timezone.utc).date()),
            "finalists": statuses["finalist"],
            "statuses": statuses,
            "missions": missions,
        })


@app.get("/api/admin/applications")
@admin_required
def admin_applications():
    query = select(ChallengeApplication).order_by(ChallengeApplication.submitted_at.desc())
    status = request.args.get("status", "").strip()
    search = request.args.get("q", "").strip()
    if status in STATUSES:
        query = query.where(ChallengeApplication.status == status)
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(
            ChallengeApplication.team_name.ilike(pattern),
            ChallengeApplication.project_title.ilike(pattern),
            ChallengeApplication.tracking_code.ilike(pattern),
            ChallengeApplication.leader_email.ilike(pattern),
        ))
    with session_scope() as db:
        items = db.scalars(query.limit(500)).all()
        return response([item.to_dict() for item in items])


@app.get("/api/admin/applications/<int:application_id>")
@admin_required
def admin_application_detail(application_id):
    with session_scope() as db:
        application = db.get(ChallengeApplication, application_id)
        if not application:
            return response(message="Заявка не найдена", status=404)
        return response(application.to_dict(detailed=True))


@app.patch("/api/admin/applications/<int:application_id>")
@admin_required
def update_application(application_id):
    payload = request.get_json(silent=True) or {}
    status = str(payload.get("status", ""))
    if status not in STATUSES:
        return response(message="Недопустимый статус", status=400)
    with session_scope() as db:
        application = db.get(ChallengeApplication, application_id)
        if not application:
            return response(message="Заявка не найдена", status=404)
        application.status = status
        application.reviewer_note = str(payload.get("reviewer_note", "")).strip()[:4000] or None
        application.updated_at = datetime.now(timezone.utc)
    return response(message="Изменения сохранены")


@app.get("/api/admin/uploads/<int:upload_id>")
@admin_required
def download_upload(upload_id):
    with session_scope() as db:
        upload = db.get(ApplicationUpload, upload_id)
        if not upload:
            abort(404)
        path = UPLOAD_FOLDER / upload.stored_name
        if not path.exists():
            abort(404)
        return send_file(path, as_attachment=True, download_name=upload.original_name, mimetype=upload.content_type)


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:page>")
def frontend(page):
    safe_pages = {"apply": "apply.html", "status": "status.html", "admin": "admin.html"}
    if page in safe_pages:
        return send_from_directory(FRONTEND_DIR, safe_pages[page])
    asset = Path(page)
    if len(asset.parts) == 1 and asset.suffix.lower() in {".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp"}:
        return send_from_directory(FRONTEND_DIR, page)
    abort(404)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
