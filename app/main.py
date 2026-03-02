import os
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue

from app.database import SessionLocal, engine
from app.models import Base, Task
from app.schemas import TaskResponse
from app.services.video_processor import process_video_task_job
from app.config import UPLOAD_DIR, OUTPUT_DIR

Base.metadata.create_all(bind=engine)

app = FastAPI()

redis_conn = Redis(host="localhost", port=6379)
queue = Queue("video_queue", connection=redis_conn)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/upload", response_model=TaskResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1️⃣ Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    upload_folder = os.path.join(UPLOAD_DIR, timestamp)
    output_folder = os.path.join(OUTPUT_DIR, timestamp)

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    file_path = os.path.join(upload_folder, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    task = Task(
        status="queued",
        input_path=file_path,
        folder_name=timestamp   # 👈 important
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    queue.enqueue(process_video_task_job, task.id, job_timeout=None)

    return task


@app.get("/task/{task_id}", response_model=TaskResponse)
def get_status(task_id: int, db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.id == task_id).first()


@app.get("/download/{task_id}")
def download_video(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    return FileResponse(task.output_path, media_type="video/mp4")