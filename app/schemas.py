from typing import List
from pydantic import BaseModel


class FileBase(BaseModel):
    filename: str
    content: str


class FileCreate(FileBase):
    pass


class File(FileBase):
    id: int

    class Config:
        orm_mode = True


class Analysis(BaseModel):
    id: int
    result: str

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    files: List[File] = []
    analyses: List[Analysis] = []

    class Config:
        orm_mode = True
