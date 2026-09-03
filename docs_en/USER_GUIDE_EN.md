# Moodle Test Converter — User Guide

A desktop tool for converting test files into Moodle formats and building
complete course backups. **Interface: Ukrainian 🇺🇦 / English 🇬🇧**
(switch in the top‑right corner; the UI rebuilds instantly).

---

## Tabs overview

| Tab | Purpose |
|---|---|
| 🔄 **Converter** | Convert raw test files to GIFT / Moodle XML / Aiken |
| 👥 **Student lists** | Build group enrollment lists (Moodle CSV) |
| ✨ **Test generation (LLM)** | Generate tests with an LLM |
| 🌿 **Branching scenarios** | Generate decision‑tree scenarios, export GIFT/H5P/JSON |
| 🔗 **Moodle API** | Import/export via Moodle Web Services |
| 📦 **Course builder** | Build a full `.mbz` course backup |

---

## 🔄 Converter

**Supported input:** `.txt`, `.docx`, `.doc`, `.xlsx`, `.csv`, `.html`

**Marking the correct answer** (any of these):
- star at the end: `b) Kyiv *`
- marker at the start: `* b) Kyiv`, `+ b) Kyiv`, `✓ b) Kyiv`
- **bold** / underlined / red / highlighted text
- answer key: `ANSWER: B`, `Відповідь: Б`, `Відповіді: 1-а, 2-б`
- exam‑dump format: `newTem;` / `QuestName:` / `trueNum:3`

**Answer mode:** *Multiple correct* (auto‑detect from markup) or *Single
correct* (only the first marked option).

**Output:** GIFT (`.txt`), Moodle XML (`.xml`), Aiken (`.txt`).

> **`.doc` note:** legacy Word 97‑2003 files are read with forced UTF‑8,
> so Cyrillic is preserved. The tool detects and rejects garbled output
> (`?????`) and strips binary "hieroglyph" noise from the document tail.

---

## 📦 Course builder (.mbz)

Builds a complete Moodle course backup from a batch of raw test files.

**Step 1 — Global quiz settings (set once per course):**
- Course name, session label (Session / Topic / Week / Module / Lesson)
- Time limit (min, 0 = no limit), attempts (0 = unlimited)
- Grading method (highest / average / last / first)
- Pass grade (%)
- Shuffle answer options
- **Random questions per quiz** (0 = all questions, in order; N > 0 =
  each quiz draws N random questions from its own category — all
  questions stay in the bank)
- Review mode: standard / strict / full

**Step 2 — Add raw files** by dragging files/folders into the list, or
with "Add raw files…" / "Add folder". All formats are supported; non‑txt
files are converted automatically.

**Step 3 (optional) — Topic list:** one line per session overrides the
file name as the session title.

**Step 4 — Output format:**
- **Full Moodle course (.mbz)** — a complete backup (sections + quizzes +
  gradebook). Import: Course administration → **Restore** → choose `.mbz`
- **Question bank (Moodle XML)** — hierarchical categories. Import:
  Question bank → Import → Moodle XML

**Step 5 — "⚙ BUILD COURSE".**

Technical spec: `docs_en/MOODLE_MBZ_SPECIFICATION_EN.md`.

---

## 🌿 Branching scenarios

Generate an interactive decision‑tree scenario with any LLM.

1. Choose a provider, paste the API key, load the available models.
2. Fill in topic, audience, difficulty (easy/medium/hard), learning
   objectives, scoring model.
3. Click **"🌿 GENERATE SCENARIO"**.
4. **"🌳 Show tree"** renders the hierarchical structure.

**Export formats:**
- 💾 scenario `.txt` — the raw scenario
- 💾 **GIFT** for Moodle — the `MOODLE_GIFT_EXPORT` section
- 🎓 **H5P (.h5p)** — a complete H5P Branching Scenario package ready to
  upload in Moodle (Interactive content → Upload)
- 📄 **JSON** — a universal `branching-scenario/1.0` document

---

## ✨ Test generation (LLM)

1. Pick a provider (free and paid options are marked).
2. Paste your API key and click **"Check key / Load models"** — the list
   of models available for your key is fetched from the server.
3. Choose a model, set topic, question count, type, difficulty, number
   of options.
4. Click **"✨ GENERATE TESTS"**, then export to GIFT/Aiken or send to
   the converter.

---

## Command line

```bash
# Convert a file to GIFT
python moodle_converter_gui.py tests.txt --format gift --outdir out

# Force single-correct mode
python moodle_converter_gui.py tests.txt --format xml --single

# Batch-convert a folder
python moodle_converter_gui.py folder/ --format xml
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `.txt` output shows `?????` | Re‑convert from the original `.doc` — the old export lost Cyrillic; this build reads `.doc` with forced UTF‑8 |
| Hieroglyphs at the end of `.doc` text | Fixed: the binary fallback now strips CJK garbage and OLE stream noise |
| Quiz empty after Restore | Use this build — slots now use `question_reference` (fixed questions), not random `question_set_reference` |
| H5P won't upload | Use the **`.h5p`** export (not a bare `.json`) — Moodle needs the full ZIP package with `h5p.json` |
