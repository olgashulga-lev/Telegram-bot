from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from models import Player
import api
from .common_utils import check_player
import os
from pathlib import Path

router = Router()

class RegistrationState(StatesGroup):
    waiting_name = State()
    waiting_photo = State()

@router.message(Command("registration"))
async def cmd_registration_start(message: types.Message, state: FSMContext):
    if check_player(message):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    await state.set_state(RegistrationState.waiting_name)
    await message.answer("Напишите имя вашего персонажа:")

@router.message(RegistrationState.waiting_name)
async def cmd_registration_name(message: types.Message, state: FSMContext):
    if len(message.text) > 30:
        await message.answer("Имя слишком длинное! Напишите покороче.")
        return
    
    await state.update_data(name=message.text)
    await state.set_state(RegistrationState.waiting_photo)
    await message.answer("Теперь отправьте фото вашего персонажа:")

@router.message(RegistrationState.waiting_photo, F.photo)
async def cmd_registration_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото!")
        return
    
    data = await state.get_data()
    name = data.get('name', f"Игрок_{message.from_user.id}")
    
    photo_dir = Path("static/player")
    photo_dir.mkdir(parents=True, exist_ok=True)
    
    photo_path = f"static/player/{message.chat.id}_{message.from_user.id}.jpg"
    
    photo = message.photo[-1]
    file_data = await message.bot.download(photo.file_id)
    with open(photo_path, 'wb') as f:
        f.write(file_data.getvalue())
    
    player = Player(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        name=name,
        photo=photo_path
    )
    
    result = api.create_player(player)
    
    if result:
        await state.clear()
        await message.answer(f"Добро пожаловать, {name}! Теперь вы можете играть!")
    else:
        await message.answer("Произошла ошибка при регистрации. Попробуйте позже.")

@router.message(Command("cancel"), StateFilter(RegistrationState))
async def cmd_cancel_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Регистрация отменена.")