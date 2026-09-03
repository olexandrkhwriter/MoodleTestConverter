# -*- coding: utf-8 -*-
"""
Система локалізації інтерфейсу (Українська / English).
Централізований словник перекладів + перемикач мови.

Використання:
    from i18n_module import tr, set_lang, get_lang, LANGS
    label = tr("add_files")          # поточна мова
    set_lang("en")                   # перемкнути
"""

# Поточна мова (за замовчуванням — українська)
_current = "uk"

LANGS = {"uk": "Українська", "en": "English"}


def set_lang(code: str):
    global _current
    if code in LANGS:
        _current = code


def get_lang() -> str:
    return _current


def tr(key: str, **kw) -> str:
    """Повертає переклад рядка за ключем для поточної мови.
    Підтримує підстановку: tr('files_count', n=5)."""
    entry = STRINGS.get(key)
    if entry is None:
        return key
    s = entry.get(_current, entry.get("uk", key))
    if kw:
        try:
            return s.format(**kw)
        except Exception:
            return s
    return s


# ---------------------------------------------------------------------------
# СЛОВНИК ПЕРЕКЛАДІВ (ключ: {'uk': ..., 'en': ...})
# ---------------------------------------------------------------------------
STRINGS = {
    # --- заголовок / вкладки ---
    "app_title": {
        "uk": "Moodle Test Converter — повний набір інструментів",
        "en": "Moodle Test Converter — complete toolkit"},
    "tab_converter": {"uk": " 🔄 Конвертер ", "en": " 🔄 Converter "},
    "tab_students": {"uk": " 👥 Списки студентів ", "en": " 👥 Student lists "},
    "tab_llm": {"uk": " ✨ Генерація тестів (LLM) ", "en": " ✨ Test generation (LLM) "},
    "tab_branch": {"uk": " 🌿 Розгалужені сценарії ", "en": " 🌿 Branching scenarios "},
    "tab_api": {"uk": " 🔗 Moodle API ", "en": " 🔗 Moodle API "},
    "tab_course": {"uk": " 📦 Генератор курсу ", "en": " 📦 Course builder "},

    # --- конвертер ---
    "add_files": {"uk": "➕ Додати файли…", "en": "➕ Add files…"},
    "add_folder": {"uk": "📁 Додати папку", "en": "📁 Add folder"},
    "clear": {"uk": "🗑 Очистити", "en": "🗑 Clear"},
    "format_lbl": {"uk": "Формат:", "en": "Format:"},
    "category_lbl": {"uk": "Категорія:", "en": "Category:"},
    "mode_lbl": {"uk": "Режим відповідей:", "en": "Answer mode:"},
    "mode_multi": {"uk": "Декілька правильних", "en": "Multiple correct"},
    "mode_single": {"uk": "Одна правильна", "en": "Single correct"},
    "preview_btn": {"uk": "👁 Перегляд", "en": "👁 Preview"},
    "help_btn": {"uk": "❓ Довідка", "en": "❓ Help"},
    "convert_btn": {"uk": "⚙ КОНВЕРТУВАТИ ВСЕ", "en": "⚙ CONVERT ALL"},
    "files_count": {"uk": "Файлів: {n}", "en": "Files: {n}"},

    # --- студенти ---
    "st_title": {"uk": "Список студентів (по одному на рядок: Прізвище Ім'я)",
                 "en": "Student list (one per line: Surname Name)"},
    "st_group": {"uk": "Група:", "en": "Group:"},
    "st_course": {"uk": "Курс:", "en": "Course:"},
    "st_generate": {"uk": "⚙ Згенерувати CSV для Moodle",
                    "en": "⚙ Generate Moodle CSV"},

    # --- LLM ---
    "llm_provider": {"uk": "Провайдер LLM:", "en": "LLM provider:"},
    "llm_key": {"uk": "🔑 API-ключ:", "en": "🔑 API key:"},
    "llm_check": {"uk": "Перевірити ключ / Завантажити моделі",
                  "en": "Check key / Load models"},
    "llm_model": {"uk": "Модель:", "en": "Model:"},
    "llm_topic": {"uk": "Тема:", "en": "Topic:"},
    "llm_count": {"uk": "Кількість питань:", "en": "Question count:"},
    "llm_type": {"uk": "Тип:", "en": "Type:"},
    "llm_level": {"uk": "Складність:", "en": "Difficulty:"},
    "llm_generate": {"uk": "✨ ЗГЕНЕРУВАТИ ТЕСТИ", "en": "✨ GENERATE TESTS"},
    "llm_free": {"uk": "БЕЗКОШТОВНО", "en": "FREE"},
    "llm_paid": {"uk": "ПЛАТНО", "en": "PAID"},

    # --- розгалужені сценарії ---
    "br_generate": {"uk": "🌿 ЗГЕНЕРУВАТИ СЦЕНАРІЙ",
                    "en": "🌿 GENERATE SCENARIO"},
    "br_tree": {"uk": "🌳 Показати дерево", "en": "🌳 Show tree"},
    "br_save": {"uk": "💾 Зберегти сценарій (.txt)",
                "en": "💾 Save scenario (.txt)"},
    "br_gift": {"uk": "💾 Експорт GIFT для Moodle",
                "en": "💾 Export GIFT for Moodle"},
    "br_h5p": {"uk": "🎓 Експорт H5P (.h5p)", "en": "🎓 Export H5P (.h5p)"},
    "br_json": {"uk": "📄 Експорт JSON", "en": "📄 Export JSON"},
    "br_need_generate": {"uk": "Спочатку згенеруйте сценарій.",
                         "en": "Please generate a scenario first."},

    # --- Moodle API ---
    "api_url": {"uk": "URL Moodle:", "en": "Moodle URL:"},
    "api_token": {"uk": "Токен (web service token):",
                  "en": "Token (web service token):"},
    "api_test": {"uk": "🔌 Перевірити з'єднання", "en": "🔌 Test connection"},

    # --- конструктор курсу ---
    "c_settings": {"uk": " Глобальні налаштування тестування (задаються 1 раз на весь курс) ",
                   "en": " Global quiz settings (set ONCE for the whole course) "},
    "c_name": {"uk": "Назва курсу:", "en": "Course name:"},
    "c_prefix": {"uk": "Назва заняття:", "en": "Session label:"},
    "c_time": {"uk": "Час (хв, 0=без обмеж.):", "en": "Time (min, 0=no limit):"},
    "c_attempts": {"uk": "Спроб (0=необмеж.):", "en": "Attempts (0=unlimited):"},
    "c_grading": {"uk": "Оцінювання:", "en": "Grading:"},
    "c_pass": {"uk": "Прохідний бал (%):", "en": "Pass grade (%):"},
    "c_shuffle": {"uk": "Перемішувати варіанти відповідей",
                  "en": "Shuffle answer options"},
    "c_random": {"uk": "Випадкових питань у тесті (0 = усі за списком):",
                 "en": "Random questions per quiz (0 = all, in order):"},
    "c_outfmt": {"uk": " Формат вихідного файлу ", "en": " Output format "},
    "c_fmt_mbz": {"uk": "📦 Повний курс Moodle (.mbz) — резервна копія курсу (секції + тести + журнал оцінок), імпорт через Restore",
                  "en": "📦 Full Moodle course (.mbz) — course backup (sections + quizzes + gradebook), import via Restore"},
    "c_fmt_xml": {"uk": "📄 Банк питань (Moodle XML) — ієрархічні категорії, імпорт у банк питань",
                  "en": "📄 Question bank (Moodle XML) — hierarchical categories, import into question bank"},
    "c_review": {"uk": "Режим перегляду (Review options):",
                 "en": "Review mode:"},
    "c_add_files": {"uk": "📂 Додати сирі файли…", "en": "📂 Add raw files…"},
    "c_add_folder": {"uk": "📁 Додати папку з файлами",
                     "en": "📁 Add folder with files"},
    "c_drop_hint": {"uk": "⬇ Drop: .txt .doc .docx .xlsx .csv .html — усі підтримувані формати",
                    "en": "⬇ Drop: .txt .doc .docx .xlsx .csv .html — all supported formats"},
    "c_drop_title": {"uk": " Сирі файли курсу — перетягніть файли/папки сюди (масове додавання) ",
                     "en": " Course raw files — drag files/folders here (bulk add) "},
    "c_generate": {"uk": "⚙ ЗГЕНЕРУВАТИ КУРС", "en": "⚙ BUILD COURSE"},
    "c_export_raw": {"uk": "📤 Експорт сирих файлів…",
                     "en": "📤 Export raw files…"},
    "c_topics_title": {"uk": " Список тем (по одній в рядок) — підставляється в назву занять за порядком ",
                       "en": " Topic list (one per line) — used as session titles in order "},

    # --- повідомлення ---
    "msg_error": {"uk": "Помилка", "en": "Error"},
    "msg_done": {"uk": "Готово", "en": "Done"},
    "msg_language": {"uk": "Мова / Language", "en": "Language / Мова"},
}
