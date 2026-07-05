import random
import os
from pathlib import Path


def get_random_photo(folder):
    folder_path = Path(f"static/{folder}")
    if not folder_path.exists():
        return None

    files = list(folder_path.glob("*.*"))
    if not files:
        return None

    return str(random.choice(files))


def parse_time(seconds):
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        return f"{seconds // 60} мин"
    else:
        return f"{seconds // 3600} ч {seconds % 3600 // 60} мин"