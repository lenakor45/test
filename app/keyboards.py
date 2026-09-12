from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

def main_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='📅 Расписание'),KeyboardButton(text='👨‍🎓 Ученики')],[KeyboardButton(text='👨‍👩‍👧 Родители'),KeyboardButton(text='💰 Балансы')],[KeyboardButton(text='📊 Отчеты')]],resize_keyboard=True)

def lesson_actions(i:int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='✅ Провести',callback_data=f'lesson:complete:{i}'),InlineKeyboardButton(text='❌ Отменить',callback_data=f'lesson:cancel:{i}')],[InlineKeyboardButton(text='🔄 Перенести',callback_data=f'lesson:move:{i}'),InlineKeyboardButton(text='✏️ Изменить',callback_data=f'lesson:edit:{i}')],[InlineKeyboardButton(text='📝 Заметка',callback_data=f'lesson:note:{i}')]])

def date_nav(center):
    s=center.strftime('%Y-%m-%d')
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='◀️',callback_data=f'date:{(center).strftime("%Y-%m-%d")}:-1'),InlineKeyboardButton(text='Сегодня',callback_data='date:today:0'),InlineKeyboardButton(text='▶️',callback_data=f'date:{s}:1')]])

def lesson_periods():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Сегодня',callback_data='period:today'),InlineKeyboardButton(text='Завтра',callback_data='period:tomorrow')],[InlineKeyboardButton(text='Неделя',callback_data='period:week'),InlineKeyboardButton(text='Месяц',callback_data='period:month')]])

def parent_actions(i:int):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='👨‍🎓 Ученики',callback_data=f'parent:students:{i}'),InlineKeyboardButton(text='💳 Оплата',callback_data=f'parent:pay:{i}')],[InlineKeyboardButton(text='✏️ Изменить',callback_data=f'parent:edit:{i}'),InlineKeyboardButton(text='🗑 Удалить',callback_data=f'parent:delete:{i}')],[InlineKeyboardButton(text='📜 История',callback_data=f'parent:history:{i}')]])
