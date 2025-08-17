from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    files = relationship("File", back_populates="project")
    analyses = relationship("Analysis", back_populates="project")


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
