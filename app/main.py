
from fastapi import (
    FastAPI,
    Depends,
    UploadFile,
    File,
    Form,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import fuzzing, models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fuzzing Application")

# Serve templates and (optional) static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.post("/projects", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = models.Project(name=project.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/projects", response_model=list[schemas.Project])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


@app.post("/projects/{project_id}/upload-exe", response_model=schemas.File)
def upload_exe(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded file temporarily
    content = file.file.read()
    path = f"/tmp/{file.filename}"
    with open(path, "wb") as f:
        f.write(content)
    code = fuzzing.decompile_exe(path)
    db_file = models.File(filename=file.filename, content=code, project_id=project_id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@app.post("/projects/{project_id}/upload-code", response_model=schemas.File)
def upload_code(project_id: int, snippet: schemas.FileCreate, db: Session = Depends(get_db)):
    db_file = models.File(filename=snippet.filename, content=snippet.content, project_id=project_id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@app.post("/projects/{project_id}/fuzz")
def fuzz(project_id: int, db: Session = Depends(get_db)):
    file = db.query(models.File).filter(models.File.project_id == project_id).first()
    if not file:
        return {"detail": "No file uploaded"}
    targets = fuzzing.select_target_variables(file.content)
    stubbed = fuzzing.generate_stubs(file.content, targets)
    results = [fuzzing.fuzz_variable(stubbed, var) for var in targets]
    analysis = models.Analysis(result="\n".join(results), project_id=project_id)
    db.add(analysis)
    db.commit()
    return {"targets": targets, "results": results}


@app.post("/projects/{project_id}/analyze", response_model=schemas.Analysis)
def analyze(project_id: int, db: Session = Depends(get_db)):
    file = db.query(models.File).filter(models.File.project_id == project_id).first()
    if not file:
        return schemas.Analysis(id=0, result="No file")
    result = fuzzing.analyze_code(file.content)
    analysis = models.Analysis(result=result, project_id=project_id)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


@app.get("/projects/{project_id}/report")
def report(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        return {"detail": "Project not found"}
    return {
        "project": project.name,
        "files": [f.filename for f in project.files],
        "analyses": [a.result for a in project.analyses],
    }


# ------------------- Web interface routes -------------------

@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    return templates.TemplateResponse(
        "index.html", {"request": request, "projects": projects}
    )


@app.post("/projects/create")
def create_project_web(name: str = Form(...), db: Session = Depends(get_db)):
    project = models.Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return RedirectResponse(url=f"/projects/{project.id}", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_page(
    request: Request, project_id: int, message: str | None = None, db: Session = Depends(get_db)
):
    project = db.query(models.Project).get(project_id)
    if not project:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "project.html", {"request": request, "project": project, "message": message}
    )


@app.post("/projects/{project_id}/upload-code-web")
def upload_code_web(
    project_id: int,
    filename: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    db_file = models.File(filename=filename, content=content, project_id=project_id)
    db.add(db_file)
    db.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.post("/projects/{project_id}/upload-exe-web")
def upload_exe_web(
    project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    data = file.file.read()
    path = f"/tmp/{file.filename}"
    with open(path, "wb") as f:
        f.write(data)
    code = fuzzing.decompile_exe(path)
    db_file = models.File(filename=file.filename, content=code, project_id=project_id)
    db.add(db_file)
    db.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.post("/projects/{project_id}/fuzz-web")
def fuzz_web(project_id: int, db: Session = Depends(get_db)):
    file = db.query(models.File).filter(models.File.project_id == project_id).first()
    if file:
        targets = fuzzing.select_target_variables(file.content)
        stubbed = fuzzing.generate_stubs(file.content, targets)
        results = [fuzzing.fuzz_variable(stubbed, var) for var in targets]
        analysis = models.Analysis(result="\n".join(results), project_id=project_id)
        db.add(analysis)
        db.commit()
    msg = "Fuzzing complete" if file else "No file uploaded"
    return RedirectResponse(
        url=f"/projects/{project_id}?message={msg}", status_code=303
    )


@app.post("/projects/{project_id}/analyze-web")
def analyze_web(project_id: int, db: Session = Depends(get_db)):
    file = db.query(models.File).filter(models.File.project_id == project_id).first()
    if file:
        result = fuzzing.analyze_code(file.content)
        analysis = models.Analysis(result=result, project_id=project_id)
        db.add(analysis)
        db.commit()
        msg = "Analysis complete"
    else:
        msg = "No file uploaded"
    return RedirectResponse(
        url=f"/projects/{project_id}?message={msg}", status_code=303
    )


@app.get("/projects/{project_id}/report-web", response_class=HTMLResponse)
def report_web(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "report.html", {"request": request, "project": project}
    )
