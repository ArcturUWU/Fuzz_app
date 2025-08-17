from fastapi import (
    FastAPI,
    Depends,
    UploadFile,
    File,
    Form,
    Request,
    HTTPException,
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


@app.delete("/projects/{project_id}")
def delete_project_api(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        return {"detail": "Project not found"}
    db.delete(project)
    db.commit()
    return {"detail": "deleted"}


@app.delete("/projects/{project_id}/files/{file_id}")
def delete_file_api(project_id: int, file_id: int, db: Session = Depends(get_db)):
    file = (
        db.query(models.File)
        .filter(models.File.project_id == project_id, models.File.id == file_id)
        .first()
    )
    if not file:
        return {"detail": "File not found"}
    db.delete(file)
    db.commit()
    return {"detail": "deleted"}


@app.get("/projects/{project_id}/files/{file_id}", response_model=schemas.File)
def get_file_api(project_id: int, file_id: int, db: Session = Depends(get_db)):
    file = (
        db.query(models.File)
        .filter(models.File.project_id == project_id, models.File.id == file_id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@app.put("/projects/{project_id}/files/{file_id}", response_model=schemas.File)
def update_file_api(
    project_id: int, file_id: int, snippet: schemas.FileCreate, db: Session = Depends(get_db)
):
    file = (
        db.query(models.File)
        .filter(models.File.project_id == project_id, models.File.id == file_id)
        .first()
    )
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    file.filename = snippet.filename
    file.content = snippet.content
    db.commit()
    db.refresh(file)
    return file


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
    stubbed, _ = fuzzing.generate_stubs(file.content, targets)
    stats = fuzzing.fuzz_targets(stubbed, targets)
    for s in stats:
        db.add(models.FuzzStat(project_id=project_id, **s))
    db.commit()
    return {"targets": targets, "results": stats}


@app.post("/projects/{project_id}/analyze", response_model=schemas.Analysis)
def analyze(project_id: int, notes: str = "", db: Session = Depends(get_db)):
    file = db.query(models.File).filter(models.File.project_id == project_id).first()
    if not file:
        return schemas.Analysis(id=0, result="No file")
    result = fuzzing.analyze_code(file.content, notes)
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
        "fuzz_stats": [
            {
                "variable": s.variable,
                "iterations": s.iterations,
                "errors": s.errors,
                "duration": s.duration,
                "memory_kb": s.memory_kb,
                "cpu_time": s.cpu_time,
            }
            for s in project.fuzz_stats
        ],
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


@app.post("/projects/{project_id}/delete")
def delete_project_web(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if project:
        db.delete(project)
        db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/projects/{project_id}/files/{file_id}/delete")
def delete_file_web(project_id: int, file_id: int, db: Session = Depends(get_db)):
    file = (
        db.query(models.File)
        .filter(models.File.project_id == project_id, models.File.id == file_id)
        .first()
    )
    if file:
        db.delete(file)
        db.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_page(
    request: Request,
    project_id: int,
    message: str | None = None,
    stubbed: str | None = None,
    stats: list[dict] | None = None,
    analysis_result: str | None = None,
    active: str = "editor-pane",
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).get(project_id)
    if not project:
        return RedirectResponse("/", status_code=303)

    file = project.files[0] if project.files else None
    original_code = file.content if file else ""
    all_targets = (
        fuzzing.select_target_variables(original_code) if file else []
    )

    return templates.TemplateResponse(
        "project.html",
        {
            "request": request,
            "project": project,
            "message": message,
            "all_targets": all_targets,
            "targets": all_targets,
            "original_code": original_code,
            "stubbed_code": stubbed,
            "fuzz_stats": stats or project.fuzz_stats,
            "analysis_result": analysis_result,
            "active_pane": active,
        },
    )


@app.post("/projects/{project_id}/save-file")
def save_file_web(
    project_id: int,
    filename: str = Form(...),
    content: str = Form(...),
    file_id: int | None = Form(None),
    db: Session = Depends(get_db),
):
    if file_id:
        db_file = (
            db.query(models.File)
            .filter(models.File.project_id == project_id, models.File.id == file_id)
            .first()
        )
        if db_file:
            db_file.filename = filename
            db_file.content = content
    else:
        db_file = models.File(
            filename=filename, content=content, project_id=project_id
        )
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
def fuzz_web(
    request: Request,
    project_id: int,
    targets: list[str] = Form([]),
    preview: str | None = Form(None),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).get(project_id)
    file = (
        db.query(models.File).filter(models.File.project_id == project_id).first()
    )
    if not project or not file:
        return RedirectResponse("/", status_code=303)

    all_targets = fuzzing.select_target_variables(file.content)
    chosen = targets or all_targets
    stubbed, _ = fuzzing.generate_stubs(file.content, chosen)
    stats = []
    if not preview:
        stats = fuzzing.fuzz_targets(stubbed, chosen)
        for s in stats:
            db.add(models.FuzzStat(project_id=project_id, **s))
        db.commit()
        message = "Fuzzing complete"
    else:
        message = "Stubs generated"

    return templates.TemplateResponse(
        "project.html",
        {
            "request": request,
            "project": project,
            "message": message,
            "all_targets": all_targets,
            "targets": chosen,
            "original_code": file.content,
            "stubbed_code": stubbed,
            "fuzz_stats": stats,
            "active_pane": "fuzz-pane",
        },
    )


@app.post("/projects/{project_id}/analyze-web")
def analyze_web(
    request: Request,
    project_id: int,
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).get(project_id)
    file = (
        db.query(models.File).filter(models.File.project_id == project_id).first()
    )
    if not project or not file:
        return RedirectResponse("/", status_code=303)

    result = fuzzing.analyze_code(file.content, notes)
    analysis = models.Analysis(result=result, project_id=project_id)
    db.add(analysis)
    db.commit()

    return templates.TemplateResponse(
        "project.html",
        {
            "request": request,
            "project": project,
            "message": "Analysis complete",
            "all_targets": fuzzing.select_target_variables(file.content),
            "targets": fuzzing.select_target_variables(file.content),
            "original_code": file.content,
            "fuzz_stats": project.fuzz_stats,
            "analysis_result": result,
            "active_pane": "analysis-pane",
        },
    )


@app.get("/projects/{project_id}/report-web", response_class=HTMLResponse)
def report_web(request: Request, project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        "report.html", {"request": request, "project": project}
    )


@app.get("/projects/{project_id}/report-pdf")
def report_pdf(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        return RedirectResponse("/", status_code=303)

    from io import BytesIO
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont("Helvetica", 14)
    c.drawString(40, 800, f"Project: {project.name}")
    y = 760
    for f in project.files:
        c.drawString(40, y, f"File: {f.filename}")
        y -= 20
        if y < 40:
            c.showPage()
            y = 800
    for stat in project.fuzz_stats:
        if y < 80:
            c.showPage()
            y = 800
        c.drawString(
            40,
            y,
            f"Fuzz {stat.variable}: iter {stat.iterations} err {stat.errors} cpu {stat.cpu_time:.2f}s mem {stat.memory_kb:.1f}kB",
        )
        y -= 20
    c.showPage()
    c.save()
    buffer.seek(0)
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{project_id}.pdf"
        },
    )
