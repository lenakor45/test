from datetime import date, datetime, time
from enum import StrEnum
from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class LessonStatus(StrEnum):
    PLANNED='planned'; COMPLETED='completed'; CANCELLED='cancelled'; MOVED='moved'

class Parent(Base):
    __tablename__='parents'
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(200))
    contacts: Mapped[str]=mapped_column(Text, default='')
    hourly_rate_kopecks: Mapped[int]=mapped_column(BigInteger, default=0)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    students: Mapped[list['Student']]=relationship(back_populates='parent', cascade='all, delete-orphan')
    payments: Mapped[list['Payment']]=relationship(back_populates='parent', cascade='all, delete-orphan')

class Student(Base):
    __tablename__='students'
    id: Mapped[int]=mapped_column(primary_key=True)
    parent_id: Mapped[int]=mapped_column(ForeignKey('parents.id', ondelete='CASCADE'))
    name: Mapped[str]=mapped_column(String(200))
    subject: Mapped[str]=mapped_column(String(200))
    duration_minutes: Mapped[int]=mapped_column(Integer, default=60)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    parent: Mapped[Parent]=relationship(back_populates='students')
    schedules: Mapped[list['RecurringSchedule']]=relationship(back_populates='student', cascade='all, delete-orphan')
    lessons: Mapped[list['Lesson']]=relationship(back_populates='student')

class RecurringSchedule(Base):
    __tablename__='recurring_schedules'
    id: Mapped[int]=mapped_column(primary_key=True)
    student_id: Mapped[int]=mapped_column(ForeignKey('students.id', ondelete='CASCADE'))
    weekday: Mapped[int]=mapped_column(Integer) # Monday=0
    start_time: Mapped[time]=mapped_column(Time)
    duration_minutes: Mapped[int]=mapped_column(Integer)
    start_date: Mapped[date]=mapped_column(Date)
    end_date: Mapped[date|None]=mapped_column(Date, nullable=True)
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    student: Mapped[Student]=relationship(back_populates='schedules')

class Lesson(Base):
    __tablename__='lessons'
    __table_args__=(UniqueConstraint('student_id','starts_at', name='uq_lesson_student_start'),)
    id: Mapped[int]=mapped_column(primary_key=True)
    student_id: Mapped[int]=mapped_column(ForeignKey('students.id', ondelete='RESTRICT'))
    schedule_id: Mapped[int|None]=mapped_column(ForeignKey('recurring_schedules.id', ondelete='SET NULL'), nullable=True)
    starts_at: Mapped[datetime]=mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int]=mapped_column(Integer)
    status: Mapped[str]=mapped_column(String(20), default=LessonStatus.PLANNED.value)
    hourly_rate_kopecks: Mapped[int]=mapped_column(BigInteger, default=0) # snapshot at creation
    charged_kopecks: Mapped[int|None]=mapped_column(BigInteger, nullable=True) # snapshot at completion
    note: Mapped[str]=mapped_column(Text, default='')
    student: Mapped[Student]=relationship(back_populates='lessons')

class Payment(Base):
    __tablename__='payments'
    id: Mapped[int]=mapped_column(primary_key=True)
    parent_id: Mapped[int]=mapped_column(ForeignKey('parents.id', ondelete='CASCADE'))
    amount_kopecks: Mapped[int]=mapped_column(BigInteger)
    paid_on: Mapped[date]=mapped_column(Date)
    comment: Mapped[str]=mapped_column(Text, default='')
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    parent: Mapped[Parent]=relationship(back_populates='payments')

class FinancialEntry(Base):
    __tablename__='financial_entries'
    id: Mapped[int]=mapped_column(primary_key=True)
    parent_id: Mapped[int]=mapped_column(ForeignKey('parents.id', ondelete='CASCADE'))
    lesson_id: Mapped[int|None]=mapped_column(ForeignKey('lessons.id', ondelete='CASCADE'), nullable=True, unique=True)
    amount_kopecks: Mapped[int]=mapped_column(BigInteger) # negative = lesson charge
    created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[str]=mapped_column(String(300), default='')
