from aiogram import types

import api

def get_player_or_none(message: types.Message):
    player = api.get_player(message.chat.id, message.from_user.id)
    if not player:
        return None
    return player


def check_player(message: types.Message):
    return api.get_player(message.chat.id, message.from_user.id) is not None