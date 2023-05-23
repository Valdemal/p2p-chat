import json
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent.parent
LANG = None  # Inits later


def change_settings(key: str, value):
    global __settings
    __settings[key] = value
    with open('settings.json', 'w') as file:
        file.write(json.dumps(__settings))


def change_lang(language: Literal['en', 'ru', 'de']):
    global LANG
    with open(str(BASE_DIR / f'lang/{language}.json'), encoding='utf-8') as lang_file:
        LANG = json.loads(lang_file.read())


with open(str(BASE_DIR / 'settings.json'), encoding="utf-8") as settings_file:
    __settings = json.loads(settings_file.read())

change_lang(__settings['language'])
