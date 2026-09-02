# -*- coding: utf-8 -*-
"""
Універсальний модуль LLM-провайдерів для генерації тестів.
Після введення API-ключа програма звертається до сервера провайдера,
отримує список ДОСТУПНИХ моделей, і користувач обирає з наявних.

Провайдери (безплатні та платні), серпень 2026:
  • Google Gemini      — безплатний рівень (AI Studio)
  • Groq               — безплатний рівень, дуже швидкий
  • Mistral (La Plateforme) — безплатний рівень
  • OpenRouter         — агрегатор, 20+ безплатних моделей + платні
  • Cerebras           — безплатний рівень
  • OpenAI             — платний
  • Anthropic (Claude) — платний
  • OpenAI-сумісний    — будь-який власний endpoint (Ollama, LM Studio…)
"""

import json
import urllib.request
import urllib.error


class LLMError(Exception):
    pass


# ---------------------------------------------------------------------------
# Реєстр провайдерів
# ---------------------------------------------------------------------------
PROVIDERS = {
    "Google Gemini": {
        "kind": "gemini",
        "free": True,
        "models_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "gen_url": "https://generativelanguage.googleapis.com/v1beta/models/"
                   "{model}:generateContent?key={key}",
        "howto": (
            "БЕЗКОШТОВНО. 1) Відкрийте https://aistudio.google.com/apikey  "
            "2) Увійдіть через Google-акаунт  3) «Create API key» → "
            "скопіюйте ключ. Безплатний рівень: обмежена кількість "
            "запитів/хв, без банківської картки."),
    },
    "Groq": {
        "kind": "openai_compat",
        "free": True,
        "base_url": "https://api.groq.com/openai/v1",
        "howto": (
            "БЕЗКОШТОВНО. 1) Зареєструйтесь на https://console.groq.com  "
            "2) Розділ «API Keys» → «Create API Key»  3) Скопіюйте ключ "
            "(gsk_...). Безплатний рівень: ~30 запитів/хв, Llama та інші "
            "швидкі моделі, без картки."),
    },
    "Mistral (La Plateforme)": {
        "kind": "openai_compat",
        "free": True,
        "base_url": "https://api.mistral.ai/v1",
        "howto": (
            "БЕЗКОШТОВНИЙ РІВЕНЬ. 1) Створіть акаунт на "
            "https://console.mistral.ai  2) «API Keys» → «Create new key»  "
            "3) Скопіюйте ключ. Безплатний експериментальний рівень із "
            "обмеженнями; для production — платний план."),
    },
    "OpenRouter": {
        "kind": "openai_compat",
        "free": True,
        "base_url": "https://openrouter.ai/api/v1",
        "howto": (
            "БЕЗКОШТОВНО + ПЛАТНО. 1) Зареєструйтесь на "
            "https://openrouter.ai  2) https://openrouter.ai/keys → "
            "«Create Key»  3) Скопіюйте ключ (sk-or-...). Містить 20+ "
            "безплатних моделей (із позначкою «:free») і сотні платних "
            "(GPT, Claude, Gemini…) через один ключ. Без картки для "
            "безплатних моделей."),
    },
    "Cerebras": {
        "kind": "openai_compat",
        "free": True,
        "base_url": "https://api.cerebras.ai/v1",
        "howto": (
            "БЕЗКОШТОВНО. 1) Зареєструйтесь на https://cloud.cerebras.ai  "
            "2) Розділ «API Keys» → створіть ключ  3) Скопіюйте (csk-...). "
            "Дуже швидка генерація, безплатний рівень із лімітами."),
    },
    "OpenAI": {
        "kind": "openai_compat",
        "free": False,
        "base_url": "https://api.openai.com/v1",
        "howto": (
            "ПЛАТНО. 1) Створіть акаунт на https://platform.openai.com  "
            "2) Поповніть баланс (Billing)  3) «API keys» → «Create new "
            "secret key»  4) Скопіюйте ключ (sk-...). Потрібна банківська "
            "картка."),
    },
    "Anthropic (Claude)": {
        "kind": "anthropic",
        "free": False,
        "base_url": "https://api.anthropic.com/v1",
        "howto": (
            "ПЛАТНО. 1) Зареєструйтесь на https://console.anthropic.com  "
            "2) Поповніть баланс  3) «API Keys» → «Create Key»  "
            "4) Скопіюйте ключ (sk-ant-...). Потрібна банківська картка."),
    },
    "OpenAI-сумісний (власний сервер)": {
        "kind": "openai_compat",
        "free": True,
        "base_url": "",
        "custom_base": True,
        "howto": (
            "ВЛАСНИЙ ENDPOINT. Для локальних/самохостингових серверів із "
            "OpenAI-сумісним API (Ollama: http://localhost:11434/v1, "
            "LM Studio: http://localhost:1234/v1, text-generation-webui, "
            "vLLM тощо). Введіть базовий URL у поле нижче; API-ключ може "
            "бути довільним (для Ollama/LM Studio — будь-який рядок)."),
    },
}


def _http_json(url, key=None, body=None, headers=None, timeout=60,
               method=None):
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=hdrs,
                                 method=method or ("POST" if data else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")[:300]
        raise LLMError(f"HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise LLMError(f"Не вдалося з'єднатися: {e}")


# ---------------------------------------------------------------------------
# Отримання списку моделей із сервера після введення ключа
# ---------------------------------------------------------------------------
def list_models(provider: str, api_key: str, base_url: str = ""):
    """Query the provider's server for available models. Returns list[str]."""
    info = PROVIDERS[provider]
    kind = info["kind"]

    if kind == "gemini":
        url = f"{info['models_url']}?key={api_key.strip()}&pageSize=1000"
        out = _http_json(url)
        models = []
        for m in out.get("models", []):
            name = m.get("name", "").replace("models/", "")
            if "generateContent" in m.get("supportedGenerationMethods", []):
                models.append(name)
        return sorted(models) or ["gemini-2.5-flash"]

    if kind == "openai_compat":
        base = base_url.strip() or info["base_url"]
        out = _http_json(f"{base}/models",
                         headers={"Authorization": f"Bearer {api_key.strip()}"})
        models = [m.get("id") for m in out.get("data", []) if m.get("id")]
        # для OpenRouter: спочатку безплатні
        if "openrouter" in base:
            free = [m for m in models if m.endswith(":free")]
            paid = [m for m in models if not m.endswith(":free")]
            return sorted(free) + sorted(paid)
        return sorted(models)

    if kind == "anthropic":
        out = _http_json(f"{info['base_url']}/models",
                         headers={"x-api-key": api_key.strip(),
                                  "anthropic-version": "2023-06-01"})
        models = [m.get("id") for m in out.get("data", []) if m.get("id")]
        return sorted(models) or ["claude-sonnet-4-5", "claude-opus-4-1",
                                  "claude-haiku-4-5"]

    return []


# ---------------------------------------------------------------------------
# Генерація тексту (уніфікована)
# ---------------------------------------------------------------------------
def chat(provider: str, api_key: str, model: str, prompt: str,
         base_url: str = "", max_tokens: int = 8192,
         temperature: float = 0.7, timeout: int = 180) -> str:
    info = PROVIDERS[provider]
    kind = info["kind"]

    if kind == "gemini":
        url = info["gen_url"].format(model=model, key=api_key.strip())
        body = {"contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature,
                                     "maxOutputTokens": max_tokens}}
        out = _http_json(url, body=body, timeout=timeout)
        try:
            return out["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError):
            raise LLMError("Gemini повернув порожню відповідь.")

    if kind == "openai_compat":
        base = base_url.strip() or info["base_url"]
        body = {"model": model, "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        out = _http_json(f"{base}/chat/completions", body=body, timeout=timeout,
                         headers={"Authorization": f"Bearer {api_key.strip()}"})
        try:
            return out["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError):
            raise LLMError("Сервер повернув порожню відповідь.")

    if kind == "anthropic":
        body = {"model": model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        out = _http_json(f"{info['base_url']}/messages", body=body,
                         timeout=timeout,
                         headers={"x-api-key": api_key.strip(),
                                  "anthropic-version": "2023-06-01"})
        try:
            return "".join(p.get("text", "")
                           for p in out.get("content", [])).strip()
        except (KeyError, IndexError):
            raise LLMError("Claude повернув порожню відповідь.")

    raise LLMError(f"Невідомий провайдер: {provider}")


# ---------------------------------------------------------------------------
# Генерація тестів (спільний промпт конвертера)
# ---------------------------------------------------------------------------
_QTYPES = {
    "Вибір однієї відповіді": "multiple choice (one correct)",
    "Вибір кількох відповідей": "multiple response (several correct)",
    "Так/Ні": "true/false",
    "Коротка відповідь": "short answer",
    "Відповідність (matching)": "matching pairs",
    "Змішаний набір": "a mix of types",
}


# Рівні складності — реальна диференціація (когнітивна вимога + пастки)
_LEVEL_GUIDE = {
    "Легка": (
        "Когнітивний рівень: знання та розуміння (низ Bloom). "
        "Питання прості, один правильний варіант очевидний для цільової "
        "аудиторії. Дистрактори чітко хибні. Без пасток, без інформаційного "
        "шуму, одна тема на питання. Мова максимально проста."),
    "Середня": (
        "Когнітивний рівень: застосування та частково аналіз. "
        "Питання вимагають застосувати знання у ситуації, а не лише згадати "
        "факт. Додай 1-2 ПРАВДОПОДІБНІ дистрактори (типові помилки "
        "початківців), трохи інформаційного шуму, можливі питання на "
        "пріоритет/порядок дій. Правильна відповідь не є очевидною без "
        "розуміння матеріалу."),
    "Складна": (
        "Когнітивний рівень: аналіз, оцінка, синтез (верх Bloom). "
        "ОБОВ'ЯЗКОВО використовуй:\n"
        "  • КОГНІТИВНІ ПАСТКИ — правдоподібні, але хибні варіанти, що "
        "виглядають логічно для того, хто знає матеріал поверхово "
        "(наприклад, частково правильні твердження, переплутані причинно-"
        "наслідкові зв'язки, варіанти, що спираються на поширені міфи);\n"
        "  • застарілі/хибні практики як дистрактори (наприклад, у медицині "
        "— рекомендації, які вже скасовані чинними гайдлайнами);\n"
        "  • питання на пріоритизацію («що ПЕРШИМ», «яка дія найважливіша»), "
        "де кілька варіантів правильні за змістом, але лише один — оптимальний;\n"
        "  • суперечливі або неповні дані, необхідність зважити ризики;\n"
        "  • кілька кроків міркування у кожному питанні.\n"
        "Правильна відповідь НЕ повинна бути очевидною — вона вимагає "
        "глибокого розуміння та критичного аналізу."),
}


def generate_tests(provider, api_key, model, topic, n_questions=10,
                   qtype="Вибір однієї відповіді", level="Середня",
                   audience="студенти", n_options=4, language="українською",
                   with_feedback=True, extra="", base_url="") -> str:
    if not api_key.strip():
        raise LLMError("Введіть API-ключ.")
    qt = _QTYPES.get(qtype, "multiple choice")
    fb = ("Для кожного варіанта додай короткий фідбек у дужках після тексту."
          if with_feedback else "Без фідбеку до варіантів.")
    level_guide = _LEVEL_GUIDE.get(level, _LEVEL_GUIDE["Середня"])

    # Спеціальний, дуже явний блок для matching, щоб LLM не згенерувала
    # звичайні тести замість відповідності.
    if qtype == "Відповідність (matching)":
        type_block = f"""ТИП ПИТАННЯ — СУВОРО «ВІДПОВІДНІСТЬ» (matching).
ЦЕ НЕ звичайні тести з вибором однієї відповіді! Кожне питання — це
ЗАВДАННЯ НА ЗІСТАВЛЕННЯ пар. Кожен рядок-варіант містить ЛІВУ та ПРАВУ
частину, розділені стрілкою « -> ». ПРАВИЛЬНІ пари позначай зірочкою
перед літерою («*А. ліва -> права»). Всі пари в блоці — правильні
(це завдання на зіставлення, учень має з'єднати їх у правильні пари).

ОБОВ'ЯЗКОВИЙ ФОРМАТ matching-питання (точно так):
1. Зіставте <чого> з <чим>:
*А. ліва частина 1 -> права частина 1
*Б. ліва частина 2 -> права частина 2
*В. ліва частина 3 -> права частина 3

ПРИКЛАД:
1. Зіставте орган з його функцією:
*А. Серце -> Перекачування крові
*Б. Легені -> Газообмін
*В. Печінка -> Детоксикація

Згенеруй {n_questions} ТАКИХ matching-питань. НЕ пиши питання з однією
правильною відповіддю і НЕ пиши звичайні тести."""
        extra_example = """
(див. ПРИКЛАД matching-питання вище — це обов'язковий формат)"""
    else:
        type_block = f"""Тип питань: {qt}.
Для типу «Так/Ні» варіанти: «А. Так» і «Б. Ні» (познач правильний).
Для «короткої відповіді» після питання напиши рядок «Відповідь: текст».
Для «відповідності» варіанти у формі «А. ліва частина -> права частина"."""
        extra_example = """
Приклад формату (для вибору відповіді):
1. Текст питання?
А. неправильний варіант
*Б. правильний варіант
В. неправильний варіант"""

    prompt = f"""Ти — методист, який готує тестові завдання для Moodle.
Тема: «{topic}». Аудиторія: {audience}. Кількість питань: {n_questions}.
Мова: пиши ВСЕ {language}. {fb}
Додаткові вимоги: {extra or 'немає'}.

РІВЕНЬ СКЛАДНОСТІ — {level.upper()}:
{level_guide}

{type_block}

ЗАГАЛЬНИЙ ФОРМАТ ВИВОДУ (суворо, без зайвого тексту, Markdown, пояснень):
• Пронумеруй питання «1.», «2.» ...
• Варіанти з літерами «А.», «Б.», «В.», «Г.» ...
• ПРАВИЛЬНУ відповідь познач зірочкою перед літерою: «*Б. текст».
• Між питаннями — порожній рядок.
{extra_example}
"""
    text = chat(provider, api_key, model, prompt, base_url=base_url)
    if text.startswith("```"):
        text = "\n".join(text.splitlines()[1:])
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()
