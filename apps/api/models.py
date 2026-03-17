"""
SQLAlchemy ORM models for AgentReadiness.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base
import enum


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# --- Enums ---

class SiteStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    READY = "READY"
    ERROR = "ERROR"


class AnalysisStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PlanTier(str, enum.Enum):
    FREE = "free"
    REPORT = "report"


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"


# --- Models ---

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(255))
    github_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    tier: Mapped[str] = mapped_column(String(20), default=PlanTier.FREE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    users: Mapped[list["User"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    sites: Mapped[list["Site"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="users")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    url: Mapped[str] = mapped_column(String(2048))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default=SiteStatus.PENDING.value)
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id"))
    sitemap_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    verification_token: Mapped[str] = mapped_column(String(36), default=new_uuid)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization: Mapped["Organization"] = relationship(back_populates="sites")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="site", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"))
    status: Mapped[str] = mapped_column(String(20), default=AnalysisStatus.QUEUED.value)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Score fields (populated on completion)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    components: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    query_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pass_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    site: Mapped["Site"] = relationship(back_populates="analyses")
    query_results: Mapped[list["QueryResult"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class QueryResult(Base):
    __tablename__ = "query_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id"))
    query_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50))
    difficulty: Mapped[str] = mapped_column(String(20))
    passed: Mapped[bool] = mapped_column(Boolean)
    confidence: Mapped[float] = mapped_column(Float)
    generated_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_chunks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0)
    retrieval_precision: Mapped[float] = mapped_column(Float, default=0.0)
    citation_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    code_valid: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    analysis: Mapped["Analysis"] = relationship(back_populates="query_results")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    site_id: Mapped[str] = mapped_column(String(36), ForeignKey("sites.id"))
    analysis_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("analyses.id"), nullable=True)
    priority: Mapped[int] = mapped_column(Integer)
    impact: Mapped[str] = mapped_column(String(20))
    effort: Mapped[str] = mapped_column(String(20))
    category: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    affected_pages: Mapped[list] = mapped_column(JSON, default=list)
    before_example: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_example: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_score_improvement: Mapped[float | None] = mapped_column(Float, nullable=True)
    implementation_status: Mapped[str] = mapped_column(String(20), default=RecommendationStatus.PENDING.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    site: Mapped["Site"] = relationship(back_populates="recommendations")


class Assessment(Base):
    """Stores free assessment results and optimization job tracking."""
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    url: Mapped[str] = mapped_column(String(2048))
    site_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    score: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(5))
    components: Mapped[dict] = mapped_column(JSON)
    rule_results: Mapped[list | None] = mapped_column(JSON, nullable=True)  # Per-rule breakdown (20 rules)
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    pass_rate: Mapped[float] = mapped_column(Float, default=0.0)
    avg_latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    top_issues: Mapped[list] = mapped_column(JSON, default=list)
    estimated_price_eur: Mapped[int] = mapped_column(Integer, default=49)
    has_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_plan: Mapped[str | None] = mapped_column(String(20), nullable=True)
    stripe_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Optimization job tracking
    optimization_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # queued, running, complete, failed
    optimization_progress: Mapped[float] = mapped_column(Float, default=0.0)
    optimization_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    optimization_zip_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    optimization_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    optimization_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    optimization_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    optimization_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
