# Moodle Course Backup Format Specification (.mbz)

> **Spec version:** Moodle 2.0 – 4.5+ (Moodle Backup 2.x Schema)
> **Verified against a real backup:** Moodle 4.5.2 (Build: 20250210)
> **File type:** **GZIP-compressed TAR archive (`tar.gz`)** with a
> service index file `.ARCHIVE_INDEX`
> **Purpose:** Course restore/import via Web UI (`Restore`) or Moodle CLI.

---

## 1. Container requirements

1. **Archive type:** `.mbz` is a **GZIP-compressed TAR** (signature
   `1F 8B`, NOT `PK`). Moodle does NOT accept a ZIP container as `.mbz`.
2. **`.ARCHIVE_INDEX`:** the first entry in the TAR. Format:
   ```
   Moodle archive file index. Count: <N>
   <path>\t<type f|d>\t<size bytes>\t<mtime unix>
   ```
   Directories use type `d`, size `0`, mtime `?`.
3. **Root level:** all root XML files (`moodle_backup.xml`,
   `questions.xml`, etc.) and service folders (`course/`, `sections/`,
   `activities/`) **must sit directly at the archive root**.
   * Forbidden: an extra wrapping root folder inside the TAR.
4. **Encoding:** all XML files are `UTF-8` without BOM.
5. **Escaping:** XML escaping (`&amp;`, `&lt;`, `&gt;`, `&apos;`,
   `&quot;`) or `<![CDATA[...]]>`. HTML inside XML fields (summary,
   intro, questiontext with `<p>`) is fully escaped (`&lt;p&gt;`).
6. **Paths in the archive:** ASCII only (no Cyrillic file paths).
7. **NULL placeholder:** empty Moodle DB fields are written as `$@NULL@$`.

---

## 2. Filesystem hierarchy inside .mbz

```text
/
├── .ARCHIVE_INDEX                 # TAR service index (must come first!)
├── moodle_backup.xml              # Main backup manifest (element index + settings)
├── moodle_backup.log              # Backup log (may be empty)
├── questions.xml                  # Question bank (categories, questions, answers)
├── gradebook.xml                  # Gradebook (categories, formulas, grade items)
├── files.xml                      # Embedded media registry (images, attachments)
├── groups.xml                     # Groups and groupings structure
├── outcomes.xml                   # Learning outcomes / competencies
├── roles.xml                      # Global role definitions
├── scales.xml                     # Custom grading scales
├── badges.xml                     # Badges
├── completion.xml                 # Course completion state
├── grade_history.xml              # Grade history
├── users.xml                      # Users (if backed up with user data)
│
├── course/                        # Course metadata
│   ├── course.xml                 # Main course parameters (name, format, dates)
│   ├── enrolments.xml             # Course enrolment methods
│   ├── inforef.xml                # External course deps (question_categoryref)
│   ├── roles.xml                  # Course-level roles
│   ├── filters.xml                # Active course filters
│   ├── comments.xml               # Comments
│   ├── calendar.xml               # Calendar events
│   ├── contentbank.xml            # H5P content bank
│   ├── completiondefaults.xml     # Default completion settings
│   └── competencies.xml           # Course competencies
│
├── sections/                      # Sections (topics / weeks)
│   ├── section_1/                 # Section zero (General)
│   │   ├── section.xml            # Section params (number, name, sequence)
│   │   └── inforef.xml            # In real 4.5 backups — an empty <inforef/>
│   └── section_{N}/               # Learning sections (Topic 1, Topic 2…)
│       ├── section.xml
│       └── inforef.xml
│
└── activities/                    # Course modules (quizzes, assignments…)
    └── quiz_{moduleId}/           # A single Quiz module
        ├── module.xml             # Module metadata (visibility, completion)
        ├── quiz.xml               # Quiz settings, question_instance, feedback
        ├── inforef.xml            # Quiz → question-category references
        ├── grades.xml             # Grade-item settings
        ├── roles.xml              # Local role overrides for the quiz
        ├── filters.xml            # Module filters
        ├── grade_history.xml      # Module grade history
        ├── completion.xml         # Module completion
        ├── comments.xml           # Module comments
        ├── calendar.xml           # Module calendar events
        ├── xapistate.xml          # xAPI (H5P) state
        └── competencies.xml       # Module competencies
```

---

## 3. ID mapping matrix

| Entity | Value / range | Declared (PK) | Referenced (FK) |
| :--- | :--- | :--- | :--- |
| **System Context ID** | `1` | system default | `moodle_backup.xml` |
| **Course Context ID** | `10` | `moodle_backup.xml` | `course/course.xml`, `questions.xml` |
| **Course ID** | `2` | `course/course.xml` (`id="2"`) | `moodle_backup.xml`, `gradebook.xml` |
| **Section DB ID** | `1` (general), `2..N` | `sections/section_{id}/section.xml` | `moodle_backup.xml`, `activities/quiz_{id}/module.xml` |
| **Section Number** | `0` (general), `1..N` | `sections/section_{id}/section.xml` | `activities/quiz_{id}/module.xml` |
| **Module ID** | `1..N` | `activities/quiz_{id}/module.xml` | `moodle_backup.xml`, `sections/section_{id}/section.xml` (`<sequence>`) |
| **Category ID** | `1` (top), `2..N` | `questions.xml` (`<question_category id="...">`) | `course/inforef.xml`, `activities/quiz_{id}/inforef.xml` |
| **Question Bank Entry ID** | `1001..N` | `questions.xml` (`<question_bank_entry id="...">`) | `activities/quiz_{id}/quiz.xml` (`<questionbankentryid>`) |
| **Answer ID** | `10001..N` | `questions.xml` (`<answer id="...">`) | local, inside `<question>` |
| **Grade Item ID** | `1` (course), `2..N` | `gradebook.xml` (`<grade_item id="...">`) | `activities/quiz_{id}/grades.xml` |

---

## 4. Key XML schemas

### 4.1. `moodle_backup.xml` (manifest)

The coordination file. Contains `<information>` with version/release
triplets, `<original_wwwroot>`, course IDs, `<details>` (backup type),
`<contents>` (activities, sections, course) and `<settings>` (per-root /
per-section / per-activity backup flags).

Activity entry inside `<contents>`:
```xml
<activity>
  <moduleid>1</moduleid>
  <sectionid>2</sectionid>
  <modulename>quiz</modulename>
  <title>Quiz: Topic 1</title>
  <directory>activities/quiz_1</directory>
  <insubsection></insubsection>
</activity>
```

Section entry:
```xml
<section>
  <sectionid>2</sectionid>
  <title>Topic 1: Basics</title>
  <directory>sections/section_2</directory>
  <parentcmid></parentcmid>
  <modname></modname>
</section>
```

### 4.2. `questions.xml` (Moodle 4.x structure)

Since Moodle 4.x, questions are wrapped in a three-level versioning
scheme: **`question_bank_entries → question_bank_entry →
question_version → question_versions → questions`** (status `ready`).

```xml
<question_categories>
  <question_category id="1">
    <name>top</name>
    <contextid>10</contextid>
    <contextlevel>50</contextlevel>
    <contextinstanceid>2</contextinstanceid>
    <info></info><infoformat>0</infoformat>
    <stamp>cat+stamp+top</stamp>
    <parent>0</parent><sortorder>0</sortorder>
    <idnumber>$@NULL@$</idnumber>
    <question_bank_entries>
    </question_bank_entries>
  </question_category>

  <question_category id="2">
    <name>Topic 1</name>
    <contextid>10</contextid>
    <contextlevel>50</contextlevel>
    <contextinstanceid>2</contextinstanceid>
    <info></info><infoformat>1</infoformat>
    <stamp>cat+stamp+2</stamp>
    <parent>1</parent><sortorder>1000</sortorder>
    <idnumber>$@NULL@$</idnumber>
    <question_bank_entries>
      <question_bank_entry id="1001">
        <questioncategoryid>2</questioncategoryid>
        <idnumber>$@NULL@$</idnumber>
        <ownerid>2</ownerid>
        <question_version>
          <question_versions id="1001">
            <version>1</version>
            <status>ready</status>
            <questions>
              <question id="1001">
                <parent>0</parent>
                <name>Question 1</name>
                <questiontext>Question text?</questiontext>
                <questiontextformat>1</questiontextformat>
                <generalfeedback></generalfeedback>
                <generalfeedbackformat>1</generalfeedbackformat>
                <defaultmark>1.0000000</defaultmark>
                <penalty>0.3333333</penalty>
                <qtype>multichoice</qtype>
                <length>1</length>
                <stamp>moodle+q+1001</stamp>
                <timecreated>1700000000</timecreated>
                <timemodified>1700000000</timemodified>
                <createdby>2</createdby>
                <modifiedby>2</modifiedby>
                <plugin_qtype_multichoice_question>
                  <answers>
                    <answer id="10001">
                      <answertext>Correct option</answertext>
                      <answerformat>1</answerformat>
                      <fraction>1.0000000</fraction>
                      <feedback></feedback><feedbackformat>1</feedbackformat>
                    </answer>
                    <answer id="10002">
                      <answertext>Wrong option</answertext>
                      <answerformat>1</answerformat>
                      <fraction>0.0000000</fraction>
                      <feedback></feedback><feedbackformat>1</feedbackformat>
                    </answer>
                  </answers>
                  <multichoice id="1001">
                    <layout>0</layout>
                    <single>1</single>
                    <shuffleanswers>1</shuffleanswers>
                    <correctfeedback></correctfeedback>
                    <correctfeedbackformat>1</correctfeedbackformat>
                    <partiallycorrectfeedback></partiallycorrectfeedback>
                    <partiallycorrectfeedbackformat>1</partiallycorrectfeedbackformat>
                    <incorrectfeedback></incorrectfeedback>
                    <incorrectfeedbackformat>1</incorrectfeedbackformat>
                    <answernumbering>abc</answernumbering>
                    <shownumcorrect>1</shownumcorrect>
                  </multichoice>
                </plugin_qtype_multichoice_question>
              </question>
            </questions>
          </question_versions>
        </question_version>
      </question_bank_entry>
    </question_bank_entries>
  </question_category>
</question_categories>
```

### 4.3. `activities/quiz_{id}/quiz.xml`

**CRITICAL — slot linking.** In Moodle 4.x each quiz slot is a
`question_instance`. A **fixed** question is attached with a nested
**`question_reference → questionbankentryid`** (the `question_bank_entry`
id from `questions.xml`). Using `question_set_reference` for a normal
quiz creates a *random-from-category* slot — and a restored quiz appears
**empty** because Moodle cannot resolve it to a concrete question.

```xml
<question_instances>
  <question_instance id="1001">
    <quizid>1</quizid>
    <slot>1</slot>
    <page>1</page>
    <displaynumber>$@NULL@$</displaynumber>
    <requireprevious>0</requireprevious>
    <maxmark>1.0000000</maxmark>
    <quizgradeitemid>$@NULL@$</quizgradeitemid>
    <question_reference id="1001">
      <usingcontextid>101</usingcontextid>
      <component>mod_quiz</component>
      <questionarea>slot</questionarea>
      <questionbankentryid>1001</questionbankentryid>
      <version>$@NULL@$</version>
    </question_reference>
  </question_instance>
</question_instances>
```

For a **random question** slot (N random questions from a category),
use instead:
```xml
<question_set_reference id="1001">
  <usingcontextid>101</usingcontextid>
  <component>mod_quiz</component>
  <questionarea>slot</questionarea>
  <questionscontextid>10</questionscontextid>
  <filtercondition>{"qpage":0,"cat":"2,10","qperpage":100,"cpage":1,"tabname":"editq","sortdata":[],"jointype":2,"filter":{"category":{"jointype":1,"values":["2"],"filteroptions":{"includesubcategories":""}}}}</filtercondition>
</question_set_reference>
```

Quiz-level review flags (bitmasks) include **`reviewmaxmarks`**
(mandatory in 4.5):
```xml
<reviewattempt>69888</reviewattempt>
<reviewcorrectness>4352</reviewcorrectness>
<reviewmaxmarks>69888</reviewmaxmarks>
<reviewmarks>4352</reviewmarks>
<reviewspecificfeedback>4352</reviewspecificfeedback>
<reviewgeneralfeedback>4352</reviewgeneralfeedback>
<reviewrightanswer>4352</reviewrightanswer>
<reviewoverallfeedback>4352</reviewoverallfeedback>
```

The quiz ends with empty `<overrides>`, `<grades>`, `<attempts>`.

### 4.4. `gradebook.xml`

Root category + one `grade_item` per quiz. Includes `<attributes>`,
`decimals=$@NULL@$`, `hidden` on the category, empty `grade_letters`
and `grade_settings`.

---

## 5. Quiz parameter reference

### 5.1. Review option bitmasks
Moodle encodes 4 time windows as bitmasks (DURING=1, IMMEDIATELY=16,
OPEN=256, CLOSED=4096):

* **Standard (safe):** `reviewattempt=69888`, `reviewmaxmarks=69888`,
  everything else `4352`
* **Strict (hide correct answers):** `reviewcorrectness=0`,
  `reviewrightanswer=0`, `reviewspecificfeedback=0`,
  `reviewgeneralfeedback=0`, `reviewmarks=4352`, `reviewoverallfeedback=4352`
* **Full:** all values `69904`

### 5.2. Question behaviour (`preferredbehaviour`)
`deferredfeedback` (exams), `immediatefeedback`, `interactive`,
`adaptive`, `adaptivenopenalty`

### 5.3. Grading method (`grademethod`)
`1` highest, `2` average, `3` first attempt, `4` last attempt

---

## 6. Validation checklist

1. [ ] **Container is TAR.GZ** (signature `1F 8B`), NOT zip. The first
   TAR entry is `.ARCHIVE_INDEX` with a correct `Count`.
2. [ ] Fractional numeric fields (`grademax`, `gradepass`, `fraction`)
   use 5–7 decimal places (`1.00000`, `0.3333333`).
3. [ ] `sequence` in each section lists real activity IDs (or is empty).
4. [ ] `questions.xml` uses the 4.x wrapper
   `question_bank_entries → question_bank_entry → question_version →
   question_versions → questions`; version status is `ready`.
5. [ ] `quiz.xml` slots are `question_instance` with a nested
   **`question_reference → questionbankentryid`** for fixed questions —
   NOT `question_set_reference` (that is for random only); every slot's
   `questionbankentryid` matches a real `question_bank_entry id`;
   `reviewmaxmarks` is present; trailing empty `<overrides>`, `<grades>`,
   `<attempts>`.
6. [ ] No invalid tag nesting in activity `inforef.xml`.
7. [ ] Empty Moodle DB fields are `$@NULL@$`.
8. [ ] TAR paths are ASCII-only, no wrapping root folder.
9. [ ] All XML parses cleanly with a standard parser (ElementTree).

---

## 7. H5P Branching Scenario package

A `.h5p` file is a **ZIP** archive containing:

```text
/
├── h5p.json                 # manifest: title, language, mainLibrary,
│                            # preloadedDependencies
└── content/
    └── content.json         # branchingScenario parameters
```

A bare `content.json` is NOT importable — Moodle requires the complete
`.h5p` ZIP package with the `h5p.json` manifest at the root.

`h5p.json` minimal manifest:
```json
{
  "title": "Branching Scenario",
  "language": "uk",
  "mainLibrary": "H5P.BranchingScenario",
  "embedTypes": ["div"],
  "license": "U",
  "defaultLanguage": "uk",
  "preloadedDependencies": [
    {"machineName": "H5P.BranchingScenario", "majorVersion": 1, "minorVersion": 7},
    {"machineName": "H5P.BranchingQuestion", "majorVersion": 1, "minorVersion": 0},
    {"machineName": "H5P.AdvancedText", "majorVersion": 1, "minorVersion": 1}
  ]
}
```

Import in Moodle: course → Add activity → Interactive content (H5P) →
Upload → choose the `.h5p` file.
