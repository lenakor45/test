from datetime import date, datetime, time
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select
from .db import SessionLocal
from .handlers import Form, guard, parse_money
from .models import Parent, Student, RecurringSchedule
from .services import generate_future_lessons

router=Router()

@router.message(F.text.startswith('/add_student'))
async def add_student(m:Message,state:FSMContext):
    if not await guard(m): return
    async with SessionLocal() as db: ps=(await db.scalars(select(Parent).order_by(Parent.name))).all()
    await state.update_data(parent_options={str(i+1):p.id for i,p in enumerate(ps)}); await state.set_state(Form.student_parent); await m.answer('Родитель:\n'+'\n'.join(f'{i+1}. {p.name}' for i,p in enumerate(ps)))
@router.message(Form.student_parent)
async def sp(m:Message,state:FSMContext):
    d=await state.get_data(); pid=d['parent_options'].get(m.text.strip())
    if not pid: return await m.answer('Выберите номер.')
    await state.update_data(parent_id=pid); await state.set_state(Form.student_name); await m.answer('Имя ученика:')
@router.message(Form.student_name)
async def sn(m:Message,state:FSMContext): await state.update_data(student_name=m.text); await state.set_state(Form.student_subject); await m.answer('Предмет:')
@router.message(Form.student_subject)
async def ss(m:Message,state:FSMContext): await state.update_data(subject=m.text); await state.set_state(Form.student_duration); await m.answer('Длительность, минут:')
@router.message(Form.student_duration)
async def sd(m:Message,state:FSMContext):
    try:
        d=await state.get_data(); dur=int(m.text); async with SessionLocal() as db: db.add(Student(parent_id=d['parent_id'],name=d['student_name'],subject=d['subject'],duration_minutes=dur)); await db.commit()
        await state.clear(); await m.answer('Ученик добавлен.')
    except Exception as e: await m.answer(f'Ошибка: {e}')

@router.message(F.text.startswith('/add_schedule'))
async def add_schedule(m:Message,state:FSMContext):
    if not await guard(m): return
    async with SessionLocal() as db: ss=(await db.scalars(select(Student).where(Student.active.is_(True)).order_by(Student.name))).all()
    await state.update_data(student_options={str(i+1):s.id for i,s in enumerate(ss)}); await state.set_state(Form.schedule_student); await m.answer('Ученик:\n'+'\n'.join(f'{i+1}. {s.name}' for i,s in enumerate(ss)))
@router.message(Form.schedule_student)
async def sch_student(m:Message,state:FSMContext):
    d=await state.get_data(); sid=d['student_options'].get(m.text.strip())
    if not sid: return await m.answer('Выберите номер.')
    await state.update_data(student_id=sid); await state.set_state(Form.schedule_weekday); await m.answer('День недели: 1=Пн ... 7=Вс')
@router.message(Form.schedule_weekday)
async def sch_day(m:Message,state:FSMContext):
    try: wd=int(m.text)-1; assert 0<=wd<=6; await state.update_data(weekday=wd); await state.set_state(Form.schedule_time); await m.answer('Время ЧЧ:ММ:')
    except: await m.answer('Введите 1–7.')
@router.message(Form.schedule_time)
async def sch_time(m:Message,state:FSMContext):
    try: t=datetime.strptime(m.text.strip(),'%H:%M').time(); await state.update_data(start_time=t.strftime('%H:%M')); await state.set_state(Form.schedule_duration); await m.answer('Длительность минут:')
    except: await m.answer('Формат ЧЧ:ММ')
@router.message(Form.schedule_duration)
async def sch_dur(m:Message,state:FSMContext):
    await state.update_data(duration=int(m.text)); await state.set_state(Form.schedule_start); await m.answer('Дата начала ДД.ММ.ГГГГ:')
@router.message(Form.schedule_start)
async def sch_start(m:Message,state:FSMContext):
    try: d=datetime.strptime(m.text,'%d.%m.%Y').date(); await state.update_data(start_date=d.isoformat()); await state.set_state(Form.schedule_end); await m.answer('Дата окончания ДД.ММ.ГГГГ или —:')
    except: await m.answer('Формат ДД.ММ.ГГГГ')
@router.message(Form.schedule_end)
async def sch_end(m:Message,state:FSMContext):
    try:
        d=await state.get_data(); end=None if m.text.strip()=='—' else datetime.strptime(m.text,'%d.%m.%Y').date()
        async with SessionLocal() as db:
            db.add(RecurringSchedule(student_id=d['student_id'],weekday=d['weekday'],start_time=time.fromisoformat(d['start_time']),duration_minutes=d['duration'],start_date=date.fromisoformat(d['start_date']),end_date=end)); await db.commit(); await generate_future_lessons(db)
        await state.clear(); await m.answer('Регулярное расписание создано и будущие занятия сгенерированы.')
    except Exception as e: await m.answer(f'Ошибка: {e}')
