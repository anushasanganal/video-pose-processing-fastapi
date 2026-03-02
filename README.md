# FastAPI Video Pose Processing System

This project processes videos using:

- FastAPI
- Redis
- RQ Worker
- OpenCV
- MediaPipe Pose Detection
- FFmpeg
- Multithreading

## Features

- Upload video
- Background processing using RQ
- Multi-threaded pose detection
- Video splitting and merging
- Download processed video
- Task status API

## Tech Stack

- FastAPI
- SQLAlchemy
- Redis
- RQ
- OpenCV
- MediaPipe
- FFmpeg

## How To Run

1. Start Redis
2. Run FastAPI:
   uvicorn app.main:app --reload
3. Run Worker:
   python app/worker.py