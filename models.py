from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ChallengeApplication(Base):
    __tablename__ = "challenge_applications"

    id = Column(BigInteger, primary_key=True)
    tracking_code = Column(String(24), unique=True, index=True, nullable=False)
    status = Column(String(24), nullable=False, default="submitted", index=True)
    team_name = Column(String(50), nullable=False)
    region = Column(String(80), nullable=False)
    institution = Column(String(180), nullable=False)
    leader_name = Column(String(160), nullable=False)
    leader_specialization = Column(String(180), nullable=False)
    leader_email = Column(String(254), nullable=False, index=True)
    leader_phone = Column(String(40), nullable=False)
    mission = Column(String(64), nullable=False, index=True)
    project_title = Column(String(180), nullable=False)
    idea_summary = Column(String(500), nullable=False)
    problem_statement = Column(Text, nullable=False)
    proposed_solution = Column(Text, nullable=False)
    expected_result = Column(Text, nullable=False)
    technologies = Column(Text, nullable=True)
    repository_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=False)
    mentor_name = Column(String(160), nullable=True)
    mentor_organization = Column(String(180), nullable=True)
    mentor_email = Column(String(254), nullable=True)
    consent_personal_data = Column(Boolean, nullable=False, default=False)
    consent_rules = Column(Boolean, nullable=False, default=False)
    originality_confirmed = Column(Boolean, nullable=False, default=False)
    reviewer_note = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    members = relationship("TeamMember", back_populates="application", cascade="all, delete-orphan")
    uploads = relationship("ApplicationUpload", back_populates="application", cascade="all, delete-orphan")

    def public_status(self):
        return {
            "tracking_code": self.tracking_code,
            "team_name": self.team_name,
            "project_title": self.project_title,
            "mission": self.mission,
            "status": self.status,
            "submitted_at": self.submitted_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_dict(self, detailed=False):
        data = self.public_status() | {
            "id": self.id,
            "region": self.region,
            "institution": self.institution,
            "leader_name": self.leader_name,
            "leader_email": self.leader_email,
            "leader_phone": self.leader_phone,
            "member_count": 1 + len(self.members),
        }
        if detailed:
            data.update({
                "leader_specialization": self.leader_specialization,
                "idea_summary": self.idea_summary,
                "problem_statement": self.problem_statement,
                "proposed_solution": self.proposed_solution,
                "expected_result": self.expected_result,
                "technologies": self.technologies,
                "repository_url": self.repository_url,
                "video_url": self.video_url,
                "mentor_name": self.mentor_name,
                "mentor_organization": self.mentor_organization,
                "mentor_email": self.mentor_email,
                "reviewer_note": self.reviewer_note,
                "members": [member.to_dict() for member in self.members],
                "uploads": [upload.to_dict() for upload in self.uploads],
            })
        return data


class TeamMember(Base):
    __tablename__ = "challenge_team_members"

    id = Column(BigInteger, primary_key=True)
    application_id = Column(BigInteger, ForeignKey("challenge_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(160), nullable=False)
    institution = Column(String(180), nullable=False)
    specialization = Column(String(180), nullable=False)
    email = Column(String(254), nullable=True)

    application = relationship("ChallengeApplication", back_populates="members")

    def to_dict(self):
        return {"id": self.id, "full_name": self.full_name, "institution": self.institution, "specialization": self.specialization, "email": self.email}


class ApplicationUpload(Base):
    __tablename__ = "challenge_application_uploads"

    id = Column(BigInteger, primary_key=True)
    application_id = Column(BigInteger, ForeignKey("challenge_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(40), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), unique=True, nullable=False)
    content_type = Column(String(120), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    application = relationship("ChallengeApplication", back_populates="uploads")

    def to_dict(self):
        return {"id": self.id, "category": self.category, "original_name": self.original_name, "content_type": self.content_type, "size_bytes": self.size_bytes}
