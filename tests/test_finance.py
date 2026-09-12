from datetime import date, datetime, time
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.db import Base
from app.finance import complete_lesson, lesson_cost, parent_balance, add_payment
from app.models import Parent, Student, Lesson

@pytest.fixture
async def db():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    Session=async_sessionmaker(engine,expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()

@pytest.mark.asyncio
async def test_money_math_and_idempotent_completion(db):
    assert lesson_cost(150000,90)==225000
    p=Parent(name='A',contacts='',hourly_rate_kopecks=150000); db.add(p); await db.flush()
    st=Student(parent_id=p.id,name='M',subject='math',duration_minutes=60); db.add(st); await db.flush()
    l=Lesson(student_id=st.id,starts_at=datetime.now(),duration_minutes=60,hourly_rate_kopecks=p.hourly_rate_kopecks); db.add(l); await db.flush()
    await add_payment(db,p.id,800000,date.today()); await db.commit()
    assert await complete_lesson(db,l.id)==150000; await db.commit()
    assert await parent_balance(db,p.id)==650000
    assert await complete_lesson(db,l.id)==150000; await db.commit()
    assert await parent_balance(db,p.id)==650000

@pytest.mark.asyncio
async def test_historical_snapshot_survives_price_change(db):
    p=Parent(name='A',contacts='',hourly_rate_kopecks=100000); db.add(p); await db.flush()
    st=Student(parent_id=p.id,name='M',subject='math',duration_minutes=60); db.add(st); await db.flush()
    l=Lesson(student_id=st.id,starts_at=datetime.now(),duration_minutes=60,hourly_rate_kopecks=100000); db.add(l); await db.commit()
    p.hourly_rate_kopecks=200000; await db.commit()
    assert await complete_lesson(db,l.id)==100000
