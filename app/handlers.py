from datetime import date, datetime, timedelta
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .config import settings
from .db import SessionLocal
from .finance import add_payment, complete_lesson, parent_balance
from .keyboards import main_menu, lesson_actions, lesson_periods, parent_actions
from .models import Lesson, LessonStatus, Parent, Student, RecurringSchedule
from .services import generate_future_lessons

router=Router()

class Form(StatesGroup):
    parent_name=State(); parent_contacts=State(); parent_rate=State(); parent_id=State(); payment_amount=State(); payment_date=State(); payment_comment=State(); student_name=State(); student_subject=State(); student_duration=State(); student_parent=State(); schedule_student=State(); schedule_weekday=State(); schedule_time=State(); schedule_duration=State(); schedule_start=State(); schedule_end=State(); move_date=State(); move_time=State(); note=State()

async def guard(m:Message|CallbackQuery)->bool:
    uid=m.from_user.id
    if uid!=settings.admin_telegram_id:
        if isinstance(m,Message): await m.answer('Доступ запрещен.')
        else: await m.answer('Доступ запрещен.',show_alert=True)
        return False
    return True

def rub(k:int):
    sign='−' if k<0 else ''; k=abs(k); return f'{sign}{k//100:,}'.replace(',',' ')+f' ₽'

def parse_money(s:str)->int:
    s=s.replace('₽','').replace(' ','').replace(',','.'); return int(round(float(s)*100))

@router.message(CommandStart())
async def start(m:Message):
    if await guard(m): await m.answer('Учет репетитора готов.',reply_markup=main_menu())

@router.message(F.text=='📅 Расписание')
async def schedule(m:Message):
    if not await guard(m): return
    await m.answer('Выберите период:',reply_markup=lesson_periods())

async def render_period(msg, mode):
    now=date.today(); end=now
    if mode=='tomorrow': now=end=now+timedelta(days=1)
    elif mode=='week': end=now+timedelta(days=6)
    elif mode=='month': end=(now.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1)
    async with SessionLocal() as db:
        q=select(Lesson).options(selectinload(Lesson.student)).where(Lesson.starts_at>=datetime.combine(now,datetime.min.time()),Lesson.starts_at<datetime.combine(end+timedelta(days=1),datetime.min.time())).order_by(Lesson.starts_at)
        lessons=(await db.scalars(q)).all()
    title='Сегодня' if mode=='today' else 'Завтра' if mode=='tomorrow' else 'Неделя' if mode=='week' else 'Месяц'
    lines=[f'📅 {title}']
    if not lessons: lines.append('Нет занятий.')
    for l in lessons:
        status={'planned':'🕐','completed':'✅','cancelled':'❌','moved':'🔄'}.get(l.status,'')
        lines.append(f'{status} {l.starts_at:%d.%m %H:%M} — {l.student.name}, {l.student.subject}, {l.duration_minutes} мин')
    await msg.answer('\n'.join(lines))
    for l in lessons:
        if l.status in ('planned','moved'): await msg.answer(f'{l.starts_at:%d.%m %H:%M} — {l.student.name}',reply_markup=lesson_actions(l.id))

@router.callback_query(F.data.startswith('period:'))
async def period(c:CallbackQuery):
    if not await guard(c): return
    await render_period(c.message,c.data.split(':')[1]); await c.answer()

@router.callback_query(F.data.startswith('lesson:complete:'))
async def complete(c:CallbackQuery):
    if not await guard(c): return
    lid=int(c.data.rsplit(':',1)[1])
    async with SessionLocal() as db:
        try:
            cost=await complete_lesson(db,lid); await db.commit()
            lesson=await db.get(Lesson,lid); balance=await parent_balance(db,lesson.student.parent_id)
            await c.message.answer(f'Занятие проведено. Списано {rub(cost)}. Баланс: {rub(balance)}')
        except Exception as e: await db.rollback(); await c.message.answer(f'Не удалось провести: {e}')
    await c.answer()

@router.callback_query(F.data.startswith('lesson:cancel:'))
async def cancel(c:CallbackQuery):
    if not await guard(c): return
    async with SessionLocal() as db:
        l=await db.get(Lesson,int(c.data.rsplit(':',1)[1]));
        if not l or l.status not in ('planned','moved'): await c.answer('Нельзя отменить',show_alert=True); return
        l.status=LessonStatus.CANCELLED.value; await db.commit()
    await c.message.answer('Занятие отменено. Деньги не списаны.'); await c.answer()

@router.callback_query(F.data.startswith('lesson:move:'))
async def move_start(c:CallbackQuery,state:FSMContext):
    if not await guard(c): return
    await state.update_data(lesson_id=int(c.data.rsplit(':',1)[1])); await state.set_state(Form.move_date); await c.message.answer('Новая дата (ДД.ММ.ГГГГ):'); await c.answer()

@router.message(Form.move_date)
async def move_date(m:Message,state:FSMContext):
    try: d=datetime.strptime(m.text.strip(),'%d.%m.%Y').date(); await state.update_data(move_date=d.isoformat()); await state.set_state(Form.move_time); await m.answer('Новое время (ЧЧ:ММ):')
    except ValueError: await m.answer('Формат: ДД.ММ.ГГГГ')

@router.message(Form.move_time)
async def move_time(m:Message,state:FSMContext):
    try:
        t=datetime.strptime(m.text.strip(),'%H:%M').time(); data=await state.get_data(); dt=datetime.fromisoformat(data['move_date']).replace(hour=t.hour,minute=t.minute)
        async with SessionLocal() as db:
            l=await db.get(Lesson,data['lesson_id']);
            if not l: raise ValueError('занятие не найдено')
            l.starts_at=dt; l.status=LessonStatus.MOVED.value; await db.commit()
        await m.answer('Занятие перенесено.',reply_markup=main_menu()); await state.clear()
    except Exception as e: await m.answer(f'Ошибка: {e}')

@router.message(F.text=='👨‍👩‍👧 Родители')
async def parents(m:Message):
    if not await guard(m): return
    async with SessionLocal() as db: ps=(await db.scalars(select(Parent).order_by(Parent.name))).all()
    text='👨‍👩‍👧 Родители\n\n'+'\n'.join(f'• {p.name} — {rub(p.hourly_rate_kopecks)}/ч' for p in ps) if ps else 'Родителей пока нет.'
    await m.answer(text+'\n\nДобавление: /add_parent')

@router.message(CommandStart())
async def noop(m:Message): pass

@router.message(F.text=='💰 Балансы')
async def balances(m:Message):
    if not await guard(m): return
    async with SessionLocal() as db: ps=(await db.scalars(select(Parent).order_by(Parent.name))).all(); rows=[]
    for p in ps:
        async with SessionLocal() as x: b=await parent_balance(x,p.id)
        icon='🟢' if b>=settings.low_balance_kopecks else '🟡' if b>=0 else '🔴'; rows.append(f'{p.name} — {icon} {rub(b)}')
    await m.answer('\n'.join(rows) or 'Нет родителей.')

@router.message(F.text=='👨‍🎓 Ученики')
async def students(m:Message):
    if not await guard(m): return
    async with SessionLocal() as db:
        ss=(await db.scalars(select(Student).options(selectinload(Student.parent)).order_by(Student.name))).all()
    await m.answer('\n'.join(f'👨‍🎓 {s.name} — {s.subject}, {s.duration_minutes} мин — {s.parent.name} — {"активен" if s.active else "неактивен"}' for s in ss) or 'Нет учеников.\nДобавление: /add_student')

@router.message(F.text=='📊 Отчеты')
async def reports(m:Message):
    if not await guard(m): return
    start=date.today().replace(day=1); end=date.today()+timedelta(days=1)
    async with SessionLocal() as db:
        lessons=(await db.scalars(select(Lesson).options(selectinload(Lesson.student)).where(Lesson.starts_at>=datetime.combine(start,datetime.min.time()),Lesson.starts_at<datetime.combine(end,datetime.min.time()),Lesson.status==LessonStatus.COMPLETED.value))).all()
        ps=(await db.scalars(select(Parent).order_by(Parent.name))).all()
        total_hours=sum(l.duration_minutes for l in lessons)/60; total_charged=sum(l.charged_kopecks or 0 for l in lessons); payments=0
        from sqlalchemy import func
        payments=int(await db.scalar(select(func.coalesce(func.sum(__import__('app.models',fromlist=['Payment']).Payment.amount_kopecks),0)).where(__import__('app.models',fromlist=['Payment']).Payment.paid_on>=start)))
        lines=[f'📊 {start:%d.%m}–{date.today():%d.%m}',f'Проведено: {len(lessons)}',f'Часы: {total_hours:g}',f'Начислено: {rub(total_charged)}',f'Получено оплат: {rub(payments)}']
        for p in ps: lines.append(f'• {p.name}: {rub(await parent_balance(db,p.id))}')
    await m.answer('\n'.join(lines))

@router.message(F.text.startswith('/add_parent'))
async def add_parent(m:Message,state:FSMContext):
    if not await guard(m): return
    await state.set_state(Form.parent_name); await m.answer('Имя родителя:')
@router.message(Form.parent_name)
async def parent_name(m:Message,state:FSMContext): await state.update_data(name=m.text); await state.set_state(Form.parent_contacts); await m.answer('Контакты:')
@router.message(Form.parent_contacts)
async def parent_contacts(m:Message,state:FSMContext): await state.update_data(contacts=m.text); await state.set_state(Form.parent_rate); await m.answer('Стоимость часа, ₽:')
@router.message(Form.parent_rate)
async def parent_rate(m:Message,state:FSMContext):
    try:
        async with SessionLocal() as db: db.add(Parent(name=(await state.get_data())['name'],contacts=(await state.get_data())['contacts'],hourly_rate_kopecks=parse_money(m.text))); await db.commit()
        await state.clear(); await m.answer('Родитель добавлен.',reply_markup=main_menu())
    except Exception as e: await m.answer(f'Ошибка: {e}')

@router.message(F.text.startswith('/pay'))
async def pay(m:Message,state:FSMContext):
    if not await guard(m): return
    async with SessionLocal() as db: ps=(await db.scalars(select(Parent))).all()
    await state.set_state(Form.parent_id); await state.update_data(parent_options={str(i+1):p.id for i,p in enumerate(ps)}); await m.answer('Номер родителя:\n'+'\n'.join(f'{i+1}. {p.name}' for i,p in enumerate(ps)))
@router.message(Form.parent_id)
async def pay_parent(m:Message,state:FSMContext):
    d=await state.get_data(); pid=d['parent_options'].get(m.text.strip());
    if not pid: await m.answer('Выберите номер.'); return
    await state.update_data(parent_id=pid); await state.set_state(Form.payment_amount); await m.answer('Сумма, ₽:')
@router.message(Form.payment_amount)
async def pay_amount(m:Message,state:FSMContext):
    try: await state.update_data(amount=parse_money(m.text)); await state.set_state(Form.payment_date); await m.answer('Дата (ДД.ММ.ГГГГ), пусто = сегодня:')
    except: await m.answer('Введите сумму, например 8000')
@router.message(Form.payment_date)
async def pay_date(m:Message,state:FSMContext):
    try: d=date.today() if not m.text.strip() else datetime.strptime(m.text.strip(),'%d.%m.%Y').date(); await state.update_data(paid_on=d.isoformat()); await state.set_state(Form.payment_comment); await m.answer('Комментарий (или —):')
    except: await m.answer('Формат даты: ДД.ММ.ГГГГ')
@router.message(Form.payment_comment)
async def pay_comment(m:Message,state:FSMContext):
    d=await state.get_data();
    async with SessionLocal() as db: await add_payment(db,d['parent_id'],d['amount'],date.fromisoformat(d['paid_on']),'' if m.text=='—' else m.text); await db.commit(); b=await parent_balance(db,d['parent_id'])
    await state.clear(); await m.answer(f'Оплата внесена. Баланс: {rub(b)}',reply_markup=main_menu())
