import os
import uuid
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.database import get_db, Job, Dataset
from tasks.worker import ingest_dataset, answer_question

router = APIRouter()

class QueryRequest(BaseModel):
    dataset_id: str
    question: str

@router.post("/datasets")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    # Create a job ID
    job_id = str(uuid.uuid4())
    
    # Save file temporarily
    os.makedirs("/app/data", exist_ok=True)
    temp_path = f"/app/data/temp_{job_id}.csv"
    if not os.path.exists("/app/data"):
        os.makedirs("data", exist_ok=True)
        temp_path = f"data/temp_{job_id}.csv"
        
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create job in DB
    job = Job(id=job_id, status="PENDING", job_type="INGESTION")
    db.add(job)
    db.commit()
    
    # Dispatch Celery task
    ingest_dataset.delay(job_id, temp_path, file.filename)
    
    return {"job_id": job_id, "status": "PENDING"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "id": job.id,
        "status": job.status,
        "job_type": job.job_type,
    }
    
    if job.status == "COMPLETED":
        response["result"] = job.result
    elif job.status == "FAILED":
        response["error"] = job.error
        
    return response

@router.post("/query")
def submit_query(request: QueryRequest, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, status="PENDING", job_type="QUERY", dataset_id=request.dataset_id)
    db.add(job)
    db.commit()
    
    answer_question.delay(job_id, request.dataset_id, request.question)
    
    return {"job_id": job_id, "status": "PENDING"}

@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [{"id": d.id, "name": d.name, "created_at": d.created_at} for d in datasets]
