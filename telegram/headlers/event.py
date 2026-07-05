from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import api
from .common_utils import get_player_or_none
from datetime import datetime

router = Router()

class EventState(StatesGroup):
    waiting_name = State()
    waiting_date = State()

@router.message(Command("event"))
async def cmd_event_list(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    events = api.get_events(message.chat.id)
    
    # Создаем клавиатуру с кнопкой для создания мероприятия
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ Добавить мероприятие",
                callback_data="create_event"
            )]
        ]
    )
    
    if not events:
        await message.answer(
            "📅 Мероприятий пока нет!\n\n"
            "Нажмите кнопку ниже, чтобы создать новое мероприятие.",
            reply_markup=keyboard
        )
        return
    
    text = "📅 <b>Мероприятия:</b>\n\n"
    for e in events:
        text += f"📌 <b>{e.name}</b>\n"
        text += f"   🕐 {e.datetime}\n\n"
    
    text += "\n⬇️ Нажмите кнопку ниже, чтобы создать мероприятие"
    
    await message.answer(text, reply_markup=keyboard)

# Обработчик кнопки "Добавить мероприятие"
@router.callback_query(lambda c: c.data == "create_event")
async def cmd_event_create_callback(callback: types.CallbackQuery, state: FSMContext):
    player = api.get_player(callback.message.chat.id, callback.from_user.id)
    if not player:
        await callback.answer("Сначала зарегистрируйтесь: /registration", show_alert=True)
        return
    
    await state.set_state(EventState.waiting_name)
    await callback.message.delete()  # Удаляем предыдущее сообщение
    await callback.message.answer("📝 Напишите название мероприятия:")
    await callback.answer()

@router.message(Command("event_create"))
async def cmd_event_create_start(message: types.Message, state: FSMContext):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    await state.set_state(EventState.waiting_name)
    await message.answer("📝 Напишите название мероприятия:")

@router.message(EventState.waiting_name)
async def cmd_event_create_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(EventState.waiting_date)
    await message.answer(
        "📅 Напишите дату и время в формате:\n"
        "ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
        "Пример: 25.12.2024 15:00\n\n"
        "Или нажмите /cancel для отмены"
    )

@router.message(EventState.waiting_date)
async def cmd_event_create_date(message: types.Message, state: FSMContext):
    try:
        parts = message.text.replace('.', ' ').replace(':', ' ').split()
        if len(parts) != 5:
            raise ValueError("Неверный формат")
        day, month, year, hour, minute = parts
        date_str = f"{day}.{month}.{year} {hour}:{minute}"
    except:
        await message.answer(
            "❌ Неверный формат!\n"
            "Используйте: ДД.ММ.ГГГГ ЧЧ:ММ\n\n"
            "Пример: 25.12.2024 15:00"
        )
        return
    
    data = await state.get_data()
    name = data['name']
    
    player = get_player_or_none(message)
    if not player:
        await message.answer("Вы не зарегистрированы!")
        await state.clear()
        return
    
    # Отправляем запрос в API
    result = api.create_event(
        chat_id=message.chat.id,
        user_id=player.user_id,
        name=name,
        datetime=date_str
    )
    
    await state.clear()
    
    if result:
        await message.answer(
            f"✅ <b>Мероприятие создано!</b>\n\n"
            f"📌 Название: {name}\n"
            f"🕐 Дата: {date_str}\n\n"
            f"Теперь другие игроки могут увидеть его в /event"
        )
    else:
        await message.answer(
            f"❌ Ошибка при создании мероприятия '{name}'.\n"
            "Попробуйте позже или проверьте правильность данных."
        )

@router.message(Command("cancel"), StateFilter(EventState))
async def cmd_event_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Создание мероприятия отменено.")