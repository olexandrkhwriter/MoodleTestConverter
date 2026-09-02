# Moodle Test Converter 🎓

Інструмент із графічним інтерфейсом (Tkinter) для конвертації тестових
завдань у формати Moodle та генерації повних курсів.

## Можливості

### 🔄 Конвертер тестів
- **Вхідні формати:** `.txt`, `.docx`, `.doc` (Word 97-2003), `.xlsx`,
  `.csv`, `.html`
- **Вихідні формати:** GIFT, Moodle XML, Aiken
- **Розмітка правильних відповідей:** зірочка (`*`), `+`, `✓`, жирний /
  підкреслений / кольоровий текст, ключі відповідей (`ANSWER: B`,
  `Відповіді: 1-а, 2-б`), формати дампів `newTem;` / `QuestName:` /
  `trueNum:`
- Плоскі (unlettered) списки відповідей у Word (автонумерація numId)
- Надійне читання `.doc` із примусовим UTF-8 (виправлено втрату кирилиці
  на Windows: `txt:Text (encoded):UTF8` + детектор зіпсованого тексту)
- Режим «одна правильна відповідь» / «декілька правильних»

### 📦 Генератор курсу (Moodle Backup `.mbz`)
- Масове додавання сирих файлів (drag-and-drop або кнопки)
- Глобальні налаштування тестування **один раз на курс**: час, кількість
  спроб, метод оцінювання, прохідний бал, перемішування, review-опції
  (standard / strict / full), кількість **випадкових питань** у тесті
  (0 = усі фіксовані)
- Генерація повної резервної копії курсу `.mbz` (**tar.gz** +
  `.ARCHIVE_INDEX`) у форматі **Moodle 4.5**:
  - питання — `question_bank_entries → question_version` (схема 4.x);
  - слоти тесту — `question_instance` із **`question_reference` →
    `questionbankentryid`** для фіксованих питань або
    `question_set_reference` для випадкових;
  - повне дерево: `moodle_backup.xml`, `questions.xml`, `gradebook.xml`,
    `course/`, `sections/`, `activities/quiz_N/`
- Або ієрархічний банк питань (Moodle XML)
- Експорт сирих файлів у нормалізований Aiken-`.txt`

### ✨ Генерація тестів (LLM)
- 8 провайдерів (платні та безкоштовні): Gemini, OpenAI, Anthropic,
  Mistral, Groq, OpenRouter, Together, локальні (Ollama)
- Перевірка API-ключа через сервер із завантаженням списку доступних
  моделей
- Рівні складності з когнітивними пастками та застарілими практиками
  (для медичних тестів)

### 🌿 Розгалужені сценарії (branching scenarios)
- Генерація дерева рішень через будь-який LLM (вбудований системний
  промпт українською: вузли NODE_x, кінцівки END_x, SCORE_CHANGE,
  рівні складності easy/medium/hard)
- Ієрархічне відображення дерева
- **Експорт:** GIFT (Moodle), **H5P Branching Scenario** (`content.json`),
  універсальний **JSON** (`branching-scenario/1.0`)

### 👥 Списки студентів
- Формування списків груп для зарахування (CSV для Moodle)

### 🔗 Moodle API
- Імпорт/експорт баз тестів через Moodle Web Services

## Встановлення

### Варіант A: готовий інсталятор (Windows)
Завантажте `MoodleTestConverter_Setup.exe` з розділу Releases.

### Варіант B: з вихідного коду
```bash
pip install -r requirements.txt
# для drag-and-drop у конструкторі курсів (необов'язково):
pip install tkinterdnd2
python moodle_converter_gui.py
```

CLI-режим:
```bash
python moodle_converter_gui.py тести.txt --format gift --outdir out
python moodle_converter_gui.py тести.txt --format xml --single
```

## Структура репозиторію

```
src/
  converter_core.py      # парсер вхідних форматів + експорт GIFT/XML/Aiken
  moodle_converter_gui.py# головне вікно (Tkinter, 6 вкладок)
  course_module.py       # банк питань Moodle XML із сирих файлів
  mbz_module.py          # генератор повного бекапу курсу (.mbz, tar.gz)
  branching_module.py    # розгалужені сценарії (LLM + парсер + H5P/JSON)
  llm_module.py          # універсальна робота з LLM-провайдерами
  gemini_module.py       # генерація тестів (Gemini-сумісні)
  students_module.py     # списки студентів
  moodle_api_module.py   # Moodle Web Services API
tests_uni/, tests_uni2/  # 32 тестові кейси (119+ питань)
docs/                    # документація українською (посібник, формати,
                         # специфікація .mbz, тест-кейси, changelog)
```

## Тестування

```bash
python src/test_mbz.py                  # генерація .mbz (tar.gz)
python src/test_course_integration.py   # змішані формати -> .mbz
```

Повний регресійний набір: 32 файли, 119+ питань, усі формати розмітки.

## Ліцензія

Безкоштовно для освітнього використання. Розробник не несе
відповідальності за наслідки використання (див. `LICENSE.txt`).
