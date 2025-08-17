from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship

from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    files = relationship(
        "File", back_populates="project", cascade="all, delete-orphan"
    )
    analyses = relationship(
        "Analysis", back_populates="project", cascade="all, delete-orphan"
    )
    fuzz_stats = relationship(
        "FuzzStat", back_populates="project", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content = Column(Text)  # decompiled or raw code
    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="files")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    result = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="analyses")


class FuzzStat(Base):
    __tablename__ = "fuzzstats"

    id = Column(Integer, primary_key=True, index=True)
    variable = Column(String)
    iterations = Column(Integer)
    errors = Column(Integer)
    duration = Column(Float)
    memory_kb = Column(Float)
    cpu_time = Column(Float)
    project_id = Column(Integer, ForeignKey("projects.id"))

    project = relationship("Project", back_populates="fuzz_stats")
