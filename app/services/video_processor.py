import os
import cv2
import subprocess
import threading
import mediapipe as mp
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Task

from app.config import UPLOAD_DIR, OUTPUT_DIR

class VideoProcessor:

    def __init__(self, segment_time=5):
        self.segment_time = segment_time

    # ---------------- SPLIT VIDEO ----------------
    def split_video(self, input_path, upload_dir):
        output_files = []

        os.makedirs(upload_dir, exist_ok=True)

        duration_cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]

        duration = float(subprocess.check_output(duration_cmd).decode().strip())
        parts = int(duration // self.segment_time) + 1

        for i in range(parts):
            out_file = os.path.join(upload_dir, f"part_{i}.mp4")

            subprocess.run([
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-ss", str(i * self.segment_time),
                "-t", str(self.segment_time),
                "-c:v", "libx264",
                "-c:a", "aac",
                out_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            output_files.append(out_file)

        return output_files

    # ---------------- PROCESS SINGLE CHUNK ----------------
    def process_chunk(self, input_path, output_path):
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(model_complexity=1)

        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            print("Failed to open:", input_path)
            return

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25

        # 🔴 VERY IMPORTANT — ensure output folder exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

            out.write(frame)

        cap.release()
        out.release()
        pose.close()

    # ---------------- MAIN TASK ----------------
    def process_video_task(self, task_id):

        db: Session = SessionLocal()
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            print("Task not found")
            return

        task.status = "processing"
        db.commit()

        upload_dir = os.path.join(UPLOAD_DIR, task.folder_name)
        output_dir = os.path.join(OUTPUT_DIR, task.folder_name)

        # 🔴 CREATE FOLDERS HERE
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        print("Upload Dir:", upload_dir)
        print("Output Dir:", output_dir)

        # ---------------- SPLIT ----------------
        parts = self.split_video(task.input_path, upload_dir)

        threads = []
        processed_files = []

        # ---------------- PROCESS THREADS ----------------
        for i, part in enumerate(parts):
            out_path = os.path.join(output_dir, f"processed_{i}.mp4")
            processed_files.append(out_path)

            print("Saving chunk to:", out_path)

            t = threading.Thread(
                target=self.process_chunk,
                args=(part, out_path)
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # ---------------- MERGE ----------------
        final_output = os.path.join(output_dir, "final.mp4")
        file_list_path = os.path.join(output_dir, "file_list.txt")

        with open(file_list_path, "w") as f:
            for file in processed_files:
                f.write(f"file '{os.path.abspath(file)}'\n")

        subprocess.run([
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", file_list_path,
            "-c", "copy",
            final_output
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        task.status = "completed"
        task.output_path = final_output
        db.commit()
        db.close()

        print("TASK COMPLETED")


# ---------------- RQ ENTRY FUNCTION ----------------
def process_video_task_job(task_id: int):
    processor = VideoProcessor()
    processor.process_video_task(task_id)