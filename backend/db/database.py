from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from core.config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, index=True)
    status = Column(String, index=True) # PENDING, PROCESSING, COMPLETED, FAILED
    job_type = Column(String) # INGESTION, QUERY
    dataset_id = Column(String, index=True, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    schema_info = Column(JSON) # Stores inferred schema
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
