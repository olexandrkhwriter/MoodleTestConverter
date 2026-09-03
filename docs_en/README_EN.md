# Moodle Test Converter 🎓

A desktop toolkit (Tkinter GUI + CLI) for converting test files into
Moodle‑ready formats and for generating complete Moodle course backups.

**Interface languages:** Ukrainian 🇺🇦 and English 🇬🇧 — switchable at
runtime from the language selector in the top‑right corner. The whole UI
is rebuilt in the chosen language without restarting.

---

## Features

### 🔄 Test converter
- **Input formats:** `.txt`, `.docx`, `.doc` (Word 97‑2003), `.xlsx`,
  `.csv`, `.html`
- **Output formats:** GIFT, Moodle XML, Aiken
- **Correct‑answer markup:** star (`*`), `+`, `✓`, bold / underlined /
  red‑font / highlighted text, answer keys (`ANSWER: B`,
  `Відповіді: 1-а, 2-б`), exam‑dump formats `newTem;` / `QuestName:` /
  `trueNum:`
- Plain (unlettered) option lists in Word (auto‑numbered `numId` lists)
- Robust `.doc` reading with forced UTF‑8 — fixes Cyrillic loss on
  Windows (`txt:Text (encoded):UTF8`) and a crude binary fallback that
  strips CJK‑hieroglyph garbage and OLE stream noise from the document tail
- Answer mode: single correct / multiple correct answers

### 📦 Course builder (Moodle backup `.mbz`)
- Bulk‑add raw files (drag‑and‑drop or buttons)
- Global quiz settings set **once per course**: time limit, attempts,
  grading method, pass grade, answer shuffling, review options
  (standard / strict / full), **number of random questions per quiz**
  (0 = all questions fixed, in order)
- Generates a complete course backup `.mbz` (**tar.gz** +
  `.ARCHIVE_INDEX`) in **Moodle 4.5** format:
  - questions use the 4.x wrapper `question_bank_entries →
    question_version → question_versions`;
  - quiz slots use `question_instance` with **`question_reference` →
    `questionbankentryid`** for fixed questions, or
    `question_set_reference` for random‑from‑category questions;
  - full tree: `moodle_backup.xml`, `questions.xml`, `gradebook.xml`,
    `course/`, `sections/`, `activities/quiz_N/`
- Or a hierarchical question bank (Moodle XML)
- Export raw files to normalized Aiken `.txt`

### ✨ Test generation (LLM)
- 8 providers (free and paid): Gemini, OpenAI, Anthropic, Mistral, Groq,
  OpenRouter, Together, local (Ollama)
- API‑key validation against the server with live model‑list download
- Difficulty levels with cognitive traps and outdated‑practice distractors
  (for medical tests)

### 🌿 Branching scenarios
- Decision‑tree generation via any LLM (built‑in Ukrainian system prompt:
  `NODE_x` nodes, `END_x` endings, `SCORE_CHANGE`, easy/medium/hard)
- Hierarchical tree view
- **Export:** GIFT (Moodle), **H5P Branching Scenario** (a complete
  `.h5p` ZIP package with `h5p.json` + `content/content.json`), and a
  universal **JSON** (`branching-scenario/1.0`)

### 👥 Student lists
- Build group enrollment lists (Moodle‑ready CSV)

### 🔗 Moodle API
- Import/export of test banks via Moodle Web Services

---

## Installation

### Option A: ready installer (Windows)
Download `MoodleTestConverter_Setup.exe` from Releases.

### Option B: from source
```bash
pip install -r requirements.txt
# optional, for drag-and-drop in the course builder:
pip install tkinterdnd2
python moodle_converter_gui.py
```

### CLI
```bash
python moodle_converter_gui.py tests.txt --format gift --outdir out
python moodle_converter_gui.py tests.txt --format xml --single
```

---

## Repository layout

```
src/
  converter_core.py       # input parsers + GIFT/XML/Aiken export
  moodle_converter_gui.py # main window (Tkinter, 6 tabs, UA/EN)
  i18n_module.py          # interface localization (Ukrainian / English)
  course_module.py        # Moodle XML question bank from raw files
  mbz_module.py           # full course backup generator (.mbz, tar.gz)
  branching_module.py     # branching scenarios (LLM + parser + H5P/JSON)
  llm_module.py           # unified LLM-provider layer
  gemini_module.py        # test generation (Gemini-compatible)
  students_module.py      # student lists
  moodle_api_module.py    # Moodle Web Services API
tests_uni/, tests_uni2/   # 32 test cases (119+ questions)
docs/                     # Ukrainian documentation
docs_en/                  # English documentation
```

---

## Testing

```bash
python src/test_mbz.py                  # .mbz generation (tar.gz)
python src/test_course_integration.py   # mixed formats -> .mbz
```

Full regression set: 32 files, 119+ questions, all markup formats.

## License

Free for educational use. The author assumes no liability for any
consequences of use (see `LICENSE.txt`).
