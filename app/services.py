from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import settings
from .models import Lesson, Parent, RecurringSchedule, Student, LessonStatus

WEEKDAYS=['Пн','Вт','Ср','Чт','Пт','Сб','Вс']

def generate_dates(schedule: RecurringSchedule, until: date):
    d=max(schedule.start_date, date.today())
    while d <= until:
        if d.weekday()==schedule.weekday and (schedule.end_date is None or d <= schedule.end_date): yield d
        d += timedelta(days=1)

async def generate_future_lessons(db: AsyncSession, until: date|None=None):
    until=until or (date.today()+timedelta(days=settings.lesson_generation_days))
    schedules=(await db.scalars(select(RecurringSchedule).where(RecurringSchedule.active.is_(True)))).all()
    created=0
    for s in schedules:
        student=await db.get(Student,s.student_id)
        if not student or not student.active: continue
        parent=await db.get(Parent,student.parent_id)
        for d in generate_dates(s,until):
            starts=datetime.combine(d,s.start_time)
            exists=await db.scalar(select(Lesson.id).where(Lesson.student_id==student.id,Lesson.starts_at==starts))
            if exists: continue
            db.add(Lesson(student_id=student.id,schedule_id=s.id,starts_at=starts,duration_minutes=s.duration_minutes,hourly_rate_kopecks=parent.hourly_rate_kopecks,status=LessonStatus.PLANNED.value))
            created += 1
    await db.commit(); return created

async def apply_schedule_change(db: AsyncSession, schedule_id:int, *, weekday:int, start_time, duration_minutes:int, start_date:date, end_date:date|None, future_only=True):
    s=await db.get(RecurringSchedule,schedule_id)
    if not s: raise ValueError('schedule not found')
    s.weekday=weekday; s.start_time=start_time; s.duration_minutes=duration_minutes; s.start_date=start_date; s.end_date=end_date
    if future_only:
        lessons=(await db.scalars(select(Lesson).where(Lesson.schedule_id==s.id,Lesson.starts_at>=datetime.now(),Lesson.status==LessonStatus.PLANNED.value))).all()
        for lesson in lessons:
            # old future generated occurrences are removed; generator recreates new ones
            await db.delete(lesson)
    await db.commit(); return s

async def move_lesson(db:AsyncSession, lesson_id:int, new_start:datetime):
    lesson=await db.get(Lesson,lesson_id)
    if not lesson or lesson.status != LessonStatus.PLANNED.value: raise ValueError('only planned lesson can be moved')
    conflict=await db.scalar(select(Lesson.id).where(Lesson.student_id==lesson.student_id,Lesson.starts_at==new_start,Lesson.id!=lesson.id))
    if conflict: raise ValueError('time is already occupied')
    lesson.starts_at=new_start; lesson.status=LessonStatus.MOVED.value
    await db.commit(); return lesson
