from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import FinancialEntry, Lesson, LessonStatus, Parent, Payment

class FinanceError(Exception): pass

def lesson_cost(hourly_rate_kopecks: int, duration_minutes: int) -> int:
    if hourly_rate_kopecks < 0 or duration_minutes < 0:
        raise ValueError('rate and duration must be non-negative')
    return (hourly_rate_kopecks * duration_minutes + 30) // 60

async def parent_balance(db: AsyncSession, parent_id: int) -> int:
    payments = await db.scalar(select(func.coalesce(func.sum(Payment.amount_kopecks), 0)).where(Payment.parent_id == parent_id))
    charges = await db.scalar(select(func.coalesce(func.sum(-FinancialEntry.amount_kopecks), 0)).where(FinancialEntry.parent_id == parent_id))
    return int(payments or 0) - int(charges or 0)

async def add_payment(db: AsyncSession, parent_id: int, amount_kopecks: int, paid_on, comment: str='') -> Payment:
    if amount_kopecks <= 0: raise FinanceError('payment must be positive')
    p = Payment(parent_id=parent_id, amount_kopecks=amount_kopecks, paid_on=paid_on, comment=comment)
    db.add(p); await db.flush(); return p

async def complete_lesson(db: AsyncSession, lesson_id: int) -> int:
    lesson = await db.get(Lesson, lesson_id, with_for_update=True)
    if lesson is None: raise FinanceError('lesson not found')
    if lesson.status == LessonStatus.COMPLETED.value:
        return int(lesson.charged_kopecks or 0)
    if lesson.status != LessonStatus.PLANNED.value:
        raise FinanceError('only planned lessons can be completed')
    cost = lesson_cost(lesson.hourly_rate_kopecks, lesson.duration_minutes)
    lesson.status = LessonStatus.COMPLETED.value
    lesson.charged_kopecks = cost
    db.add(FinancialEntry(parent_id=lesson.student.parent_id, lesson_id=lesson.id, amount_kopecks=-cost, description=f'Занятие #{lesson.id}'))
    await db.flush()
    return cost
