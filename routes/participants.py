from flask import request
from flask_restful import Resource
from models import Participant
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config import DATABASE_URI

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


class ParticipantResource(Resource):

    # GET all participants
    def get(self):
        session = Session()
        participants = session.query(Participant).all()

        result = [
            {
                "id": p.id,
                "name": p.name,
                "email": p.email,
                "team_id": p.team_id
            }
            for p in participants
        ]

        session.close()
        return result, 200


    # POST new participant
    def post(self):
        args = request.get_json()

        if not args:
            return {"message": "No JSON provided"}, 400

        name = args.get("name")
        email = args.get("email")
        team_id = args.get("team_id")

        if not name or not team_id:
            return {"message": "name and team_id are required"}, 400

        session = Session()

        participant = Participant(
            name=name,
            email=email,
            team_id=team_id
        )

        session.add(participant)
        session.commit()

        participant_id = participant.id
        session.close()

        return {"message": "Participant created", "id": participant_id}, 201