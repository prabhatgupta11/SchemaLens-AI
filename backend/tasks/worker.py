import os
import uuid
import json
from celery import Celery
from core.config import settings
from db.database import SessionLocal, Job, Dataset
from analytics.engine import AnalyticsEngine
from llm.agent import DataAgent

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task(name="ingest_dataset", bind=True)
def ingest_dataset(self, job_id: str, file_path: str, original_filename: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return

    job.status = "PROCESSING"
    db.commit()

    try:
        dataset_id = str(uuid.uuid4())
        engine = AnalyticsEngine(dataset_id=dataset_id)
        
        # Ingest CSV
        schema_info = engine.ingest_csv(file_path)
        
        # Save dataset metadata
        dataset = Dataset(
            id=dataset_id,
            name=original_filename,
            schema_info=schema_info
        )
        db.add(dataset)
        
        # Update job
        job.status = "COMPLETED"
        job.dataset_id = dataset_id
        job.result = {"dataset_id": dataset_id, "schema": schema_info}
        db.commit()
        
    except Exception as e:
        job.status = "FAILED"
        job.error = str(e)
        db.commit()
    finally:
        # Cleanup temporary file
        if os.path.exists(file_path):
            os.remove(file_path)
        db.close()

@celery_app.task(name="answer_question", bind=True)
def answer_question(self, job_id: str, dataset_id: str, question: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return
        
    job.status = "PROCESSING"
    db.commit()
    
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError("Dataset not found")
            
        agent = DataAgent(dataset_id=dataset_id, schema_info=dataset.schema_info)
        result = agent.answer(question)
        
        job.status = "COMPLETED"
        job.result = result
        db.commit()
    except Exception as e:
        job.status = "FAILED"
        job.error = str(e)
        db.commit()
    finally:
        db.close()
