from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class RoleRecord(Base):
    __tablename__ = 'roles'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    responsibilities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    compliance_exposure: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    risk_indicators: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class RiskRecord(Base):
    __tablename__ = 'risks'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    risk_type: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class RegulationRecord(Base):
    __tablename__ = 'regulations'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    article: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    requirements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    risk_types: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_document: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class CompetencyRecord(Base):
    __tablename__ = 'competencies'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    role_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('roles.id'))
    knowledge: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    judgement: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    role: Mapped[RoleRecord | None] = relationship()


class TrainingPlanRecord(Base):
    __tablename__ = 'training_plans'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    role_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('roles.id'))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='draft')
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    role: Mapped[RoleRecord | None] = relationship()
    recommendations: Mapped[list["RecommendationRecord"]] = relationship(back_populates="training_plan")


class RecommendationRecord(Base):
    __tablename__ = 'recommendations'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    training_plan_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('training_plans.id'))
    role_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('roles.id'))
    competency_id: Mapped[str | None] = mapped_column(String(36), ForeignKey('competencies.id'))
    quarter: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(500), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    behavioural_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    activities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    role_reference: Mapped[str] = mapped_column(Text, nullable=False)
    risk_reference: Mapped[str] = mapped_column(Text, nullable=False)
    regulation_reference: Mapped[str] = mapped_column(Text, nullable=False)
    competency_reference: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    role: Mapped[RoleRecord | None] = relationship()
    competency: Mapped[CompetencyRecord | None] = relationship()
    training_plan: Mapped[TrainingPlanRecord | None] = relationship(back_populates="recommendations")


class AuditLogRecord(Base):
    __tablename__ = 'audit_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_used: Mapped[str | None] = mapped_column(String(255))
    prompt: Mapped[dict | None] = mapped_column(JSON)
    output: Mapped[dict | None] = mapped_column(JSON)
    references: Mapped[dict | None] = mapped_column(JSON)
    uploaded_docs: Mapped[dict | None] = mapped_column(JSON)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
