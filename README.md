# Moodle Test Converter 🎓

**[English](#english) | [Українська](#українська)**

A desktop toolkit (Tkinter GUI + CLI) for converting test files into
Moodle formats and generating complete Moodle course backups.

**Interface: Ukrainian 🇺🇦 / English 🇬🇧** — switchable at runtime.

---

<a name="english"></a>
## English

### Features
- **🔄 Test converter** — `.txt` / `.docx` / `.doc` / `.xlsx` / `.csv` /
  `.html` → GIFT, Moodle XML, Aiken. Correct-answer markup: `*`, `+`,
  `✓`, bold/red/highlighted text, answer keys, `QuestName:`/`trueNum:`
  exam dumps. Robust `.doc` reading with forced UTF‑8 (no Cyrillic loss,
  no binary "hieroglyph" tail).
- **📦 Course builder (.mbz)** — full Moodle 4.5 course backup
  (tar.gz + `.ARCHIVE_INDEX`): sections, quizzes, question bank,
  gradebook. Global settings set once per course, including **random
  questions per quiz**. Fixed questions use `question_reference`
  (restores correctly); random ones use `question_set_reference`.
- **✨ Test generation (LLM)** — 8 providers (Gemini, OpenAI, Anthropic,
  Mistral, Groq, OpenRouter, Together, Ollama) with live model loading.
- **🌿 Branching scenarios** — LLM-generated decision trees; export to
  GIFT, **H5P Branching Scenario (`.h5p` package)** and JSON.
- **👥 Student lists**, **🔗 Moodle API** import/export.

### Install
```bash
pip install -r requirements.txt
pip install tkinterdnd2   # optional, for drag-and-drop
python src/moodle_converter_gui.py
```

### CLI
```bash
python src/moodle_converter_gui.py tests.txt --format gift --outdir out
python src/moodle_converter_gui.py tests.txt --format xml --single
```

### Documentation
- **English:** `docs_en/` — [User guide](docs_en/USER_GUIDE_EN.md),
  [.mbz specification](docs_en/MOODLE_MBZ_SPECIFICATION_EN.md)
- **Українською:** `docs/`

---

<a name="українська"></a>
## Українська

### Можливості
- **🔄 Конвертер тестів** — `.txt` / `.docx` / `.doc` / `.xlsx` / `.csv`
  / `.html` → GIFT, Moodle XML, Aiken. Розмітка правильних: `*`, `+`,
  `✓`, жирний/кольоровий текст, ключі відповідей, дампи `QuestName:` /
  `trueNum:`. Надійне читання `.doc` із примусовим UTF‑8 (без втрати
  кирилиці та без «ієрогліфів» у кінці).
- **📦 Генератор курсу (.mbz)** — повна резервна копія курсу Moodle 4.5
  (tar.gz + `.ARCHIVE_INDEX`): секції, тести, банк питань, журнал
  оцінок. Глобальні налаштування один раз на курс, включно з кількістю
  **випадкових питань у тесті**. Фіксовані питання — через
  `question_reference` (коректний Restore), випадкові — через
  `question_set_reference`.
- **✨ Генерація тестів (LLM)** — 8 провайдерів із завантаженням моделей.
- **🌿 Розгалужені сценарії** — дерева рішень через LLM; експорт у GIFT,
  **H5P Branching Scenario (пакет `.h5p`)** та JSON.
- **👥 Списки студентів**, **🔗 Moodle API** імпорт/експорт.

### Встановлення
```bash
pip install -r requirements.txt
pip install tkinterdnd2   # опційно, для drag-and-drop
python src/moodle_converter_gui.py
```

### Документація
- **Українською:** `docs/` — посібник, формати, специфікація `.mbz`,
  тест-кейси, changelog
- **English:** `docs_en/`

---

## Repository layout

```
src/        — source code (13 modules + tests)
docs/       — Ukrainian documentation
docs_en/    — English documentation
tests_uni/, tests_uni2/  — 32 test cases (119+ questions)
```

## License

Free for educational use. No liability assumed (see `LICENSE.txt`).
