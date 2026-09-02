# -*- coding: utf-8 -*-
"""
Модуль генерації тестів та завдань за допомогою Google Gemini.
Користувач вводить API-ключ на початку. Підтримує настройки:
кількість питань, тип (вибір/так-ні/коротка/відповідність), складність,
мова, тема, аудиторія, кількість варіантів, наявність пояснень.
Результат — готовий текст у форматі, який одразу парситься конвертером
(зірочка на правильній відповіді) або GIFT.
"""

import json
import urllib.request
import urllib.error

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

_QTYPES = {
    "Вибір однієї відповіді": "multiple choice (one correct)",
    "Вибір кількох відповідей": "multiple response (several correct)",
    "Так/Ні": "true/false",
    "Коротка відповідь": "short answer",
    "Відповідність (matching)": "matching pairs",
    "Змішаний набір": "a mix of types",
}

_LEVELS = ["Легка", "Середня", "Складна"]


class GeminiError(Exception):
    pass


def _endpoint(model: str, key: str) -> str:
    return ("https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={key}")


def generate_tests(api_key: str, topic: str, n_questions: int = 10,
                   qtype: str = "Вибір однієї відповіді",
                   level: str = "Середня", audience: str = "студенти",
                   n_options: int = 4, language: str = "українською",
                   with_feedback: bool = True,
                   model: str = "gemini-2.5-flash",
                   extra: str = "") -> str:
    """
    Generate a ready-to-import test in the converter's own markup
    (star before the correct option letter), then it can be exported
    to GIFT/XML/Aiken by the main converter.
    """
    if not api_key.strip():
        raise GeminiError("Введіть API-ключ Gemini.")
    qt = _QTYPES.get(qtype, "multiple choice")
    fb = ("Для кожного варіанта додай короткий фідбек у дужках після тексту."
          if with_feedback else "Без фідбеку до варіантів.")

    prompt = f"""Ти — методист, який готує тестові завдання для Moodle.
Згенеруй {n_questions} тестових питань на тему: «{topic}».
Аудиторія: {audience}. Рівень складності: {level}. Тип: {qt}.
Кількість варіантів відповіді на питання: {n_options}.
Мова: пиши ВСЕ {language}. {fb}
Додаткові вимоги: {extra or 'немає'}.

ФОРМАТ ВИВОДУ (суворо, без зайвого тексту, Markdown чи пояснень):
Пронумеруй питання «1.», «2.» ... Після тексту питання — варіанти
з літерами «А.», «Б.», «В.», «Г.» ... ПРАВИЛЬНУ відповідь познач
зірочкою перед літерою: «*Б. текст». Між питаннями — порожній рядок.
Для типу «Так/Ні» варіанти: «А. Так» і «Б. Ні» (познач правильний).
Для «короткої відповіді» після питання напиши рядок «Відповідь: текст».
Для «відповідності» варіанти у формі «А. ліва частина -> права частина».

Приклад формату:
1. Текст питання?
А. неправильний варіант
*Б. правильний варіант
В. неправильний варіант
"""

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
    }).encode("utf-8")
    req = urllib.request.Request(_endpoint(model, api_key.strip()),
                                 data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        raise GeminiError(f"Помилка Gemini API ({e.code}): {detail}")
    except urllib.error.URLError as e:
        raise GeminiError(f"Не вдалося з'єднатися з Gemini: {e}")

    try:
        text = out["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise GeminiError("Gemini повернув порожню відповідь. "
                          "Спробуйте змінити настройки.")
    # strip possible markdown fences
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.splitlines()[1:])
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()
