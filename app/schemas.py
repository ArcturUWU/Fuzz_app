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
        from_attributes = True


class Analysis(BaseModel):
    id: int
    result: str

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    name: str


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    files: List[File] = []
    analyses: List[Analysis] = []
    fuzz_stats: List["FuzzStat"] = []

    class Config:
        from_attributes = True


class FuzzStatBase(BaseModel):
    variable: str
    iterations: int
    errors: int
    duration: float
    memory_kb: float
    cpu_time: float


class FuzzStat(FuzzStatBase):
    id: int

    class Config:
        from_attributes = True


# forward references
Project.model_rebuild()
