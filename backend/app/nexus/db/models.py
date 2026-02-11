"""SQLAlchemy models for Nexus resume scoring."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class NexusResume(Base):
    __tablename__ = "nexus_resumes"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, unique=True, index=True, nullable=False)
    latest_analysis_id = Column(Integer, ForeignKey("nexus_resume_analyses.id"), nullable=True)
    is_analyzed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    files = relationship("NexusResumeFile", back_populates="resume", cascade="all, delete-orphan")
    analyses = relationship("NexusResumeAnalysis", back_populates="resume", cascade="all, delete-orphan")
    latest_analysis = relationship("NexusResumeAnalysis", foreign_keys=[latest_analysis_id])


class NexusResumeFile(Base):
    __tablename__ = "nexus_resume_files"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, ForeignKey("nexus_resumes.resume_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    resume = relationship("NexusResume", back_populates="files")


class NexusResumeAnalysis(Base):
    __tablename__ = "nexus_resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, ForeignKey("nexus_resumes.resume_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"), nullable=False, index=True)
    job_description = Column(Text, nullable=False)
    analysis_json = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("NexusResume", back_populates="analyses")
