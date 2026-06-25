from flask import request
from flask_restful import Resource
from database import SessionLocal
from models import Application


class ApplicationResource(Resource):

    def post(self):
        data = request.get_json()

        session = SessionLocal()

        app = Application(
            team_name=data.get("team_name"),
            region=data.get("region"),
            institution=data.get("institution"),

            leader_name=data.get("leader_name"),
            leader_email=data.get("leader_email"),
            leader_phone=data.get("leader_phone"),

            mission=data.get("mission"),

            project_title=data.get("project_title"),
            description=data.get("description"),
            problem_statement=data.get("problem_statement"),
            solution=data.get("solution"),
            impact=data.get("impact"),
            technologies=data.get("technologies"),
            github=data.get("github"),

            files=data.get("files"),
            status="pending"
        )

        session.add(app)
        session.commit()

        app_id = app.id
        session.close()

        return {
            "message": "Application submitted successfully",
            "application_id": app_id
        }, 201