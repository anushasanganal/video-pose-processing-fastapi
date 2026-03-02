# from sqlalchemy import Column, Integer, String
# from .database import Base

# class Task(Base):
#     __tablename__ = "tasks"

#     id = Column(Integer, primary_key=True, index=True)
#     status = Column(String(50), default="queued")
#     input_path = Column(String(255))
#     output_path = Column(String(255))

from sqlalchemy import Column, Integer, String
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    status = Column(String(50), default="queued")
    input_path = Column(String(255))
    output_path = Column(String(255), nullable=True)
    folder_name = Column(String(100), nullable=False)