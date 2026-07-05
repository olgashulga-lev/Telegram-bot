from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import api
from .common_utils import get_player_or_none

router = Router()

class TaskState(StatesGroup):
    waiting_task_id = State()
    waiting_name = State()
    waiting_money = State()
    waiting_duration = State()


@router.message(Command("task"))
async def cmd_task_list(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    tasks = api.get_free_tasks(message.chat.id)
    
    if not tasks:
        await message.answer("Свободных заданий нет!")
        return
    
    text = "<b>Свободные задания:</b>\n\n"
    for task in tasks[:5]:
        text += f"#{task.id} {task.name}\n {task.money} монет\n\n"
    
    text += "\n/task_take [номер] - взять задание"
    await message.answer(text)


@router.message(Command("task_take"))
async def cmd_task_take(message: types.Message):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите номер задания: /task_take 1")
        return
    
    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("Номер должен быть числом!")
        return
    
    tasks = api.get_free_tasks(message.chat.id)
    task = next((t for t in tasks if t.id == task_id), None)
    
    if not task:
        await message.answer("Задание с таким номером не найдено!")
        return
    
    api.take_task(task, player.user_id)
    await message.answer(f"Вы взяли задание: {task.name}")


@router.message(Command("task_add"))
async def cmd_task_add_start(message: types.Message, state: FSMContext):
    player = get_player_or_none(message)
    if not player:
        await message.answer("Сначала зарегистрируйтесь: /registration")
        return
    
    await state.set_state(TaskState.waiting_name)
    await message.answer("Напишите название задания:")


@router.message(TaskState.waiting_name)
async def cmd_task_add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(TaskState.waiting_money)
    await message.answer("Сколько монет вы заплатите за выполнение?")


@router.message(TaskState.waiting_money)
async def cmd_task_add_money(message: types.Message, state: FSMContext):
    try:
        money = int(message.text)
        if money <= 0:
            await message.answer("Награда должна быть положительным числом!")
            return
    except ValueError:
        await message.answer("Введите число!")
        return
    
    player = get_player_or_none(message)
    if player.money < money:
        await message.answer(f"У вас недостаточно денег! Нужно: {money}, есть: {player.money}")
        return
    
    await state.update_data(money=money)
    await state.set_state(TaskState.waiting_duration)
    await message.answer("Сколько минут даётся на выполнение?")


@router.message(TaskState.waiting_duration)
async def cmd_task_add_duration(message: types.Message, state: FSMContext):
    try:
        duration = int(message.text)
        if duration <= 0:
            await message.answer("Время должно быть положительным!")
            return
    except ValueError:
        await message.answer("Введите число!")
        return
    
    data = await state.get_data()
    name = data['name']
    money = data['money']
    
    player = get_player_or_none(message)
    if not player:
        await message.answer("Вы не зарегистрированы!")
        await state.clear()
        return
    
    # Списываем деньги
    player.money -= money
    api.update_player(player)
    
    # ✅ СОЗДАЁМ ЗАДАНИЕ В БАЗЕ ДАННЫХ
    result = api.create_task(
        chat_id=message.chat.id,  # передаем chat_id
        owner_id=player.user_id,  # передаем owner_id
        name=name,
        money=money,
        duration=duration
    )
    
    await state.clear()
    
    if result:
        await message.answer(
            f"✅ Задание '{name}' создано!\n"
            f"💰 Награда: {money} монет\n"
            f"⏱️ Время: {duration} мин\n\n"
            f"Другие игроки могут взять его через /task"
        )
    else:
        # Если не получилось - возвращаем деньги
        player.money += money
        api.update_player(player)
        await message.answer("❌ Ошибка при создании задания. Попробуйте позже.")


@router.message(Command("cancel"), StateFilter(TaskState))
async def cmd_cancel_task(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Создание задания отменено.")