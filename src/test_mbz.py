# -*- coding: utf-8 -*-
"""Функціональний тест mbz_module: сирі файли -> MbzCourse -> .mbz (tar.gz).
Формат перевірено на реальному бекапі Moodle 4.5.2 (IFNMU)."""
import gzip
import io
import os
import sys
import tarfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from course_module import GlobalSettings
from mbz_module import MbzBuilder, build_mbz_from_files, files_to_course

# --- тестові сирі Aiken-файли -------------------------------------------
os.makedirs("/tmp/mbz_raw", exist_ok=True)
FILES = {
    "01_вступ.txt": (
        "Що таке домедична допомога?\n"
        "A. Операція в умовах стаціонару\n"
        "B. Комплекс найпростіших медичних заходів\n"
        "C. Консультація лікаря\n"
        "D. Лабораторне дослідження\n"
        "ANSWER: B\n"
        "\n"
        "Співвідношення компресій до вдихів при СЛР дорослого?\n"
        "A. 15:2\n"
        "B. 5:1\n"
        "C. 30:2\n"
        "D. 10:1\n"
        "ANSWER: C\n"),
    "02_судоми.txt": (
        "Дії при генералізованому судомному нападі?\n"
        "A. Стримувати кінцівки\n"
        "B. Вставити предмет між зубами\n"
        "C. Захистити голову, повернути набік після нападу\n"
        "D. Дати води\n"
        "ANSWER: C\n"),
    "10_кровотеча.txt": (
        "Перша дія при масивній зовнішній кровотечі?\n"
        "A. Накласти пов'язку\n"
        "B. Прямий тиск на рану\n"
        "C. Дати знеболювальне\n"
        "D. Транспортувати негайно\n"
        "ANSWER: B\n"),
    "порожній.txt": "тут немає жодного питання у форматі Aiken\n",
}
for name, body in FILES.items():
    with open(os.path.join("/tmp/mbz_raw", name), "w",
              encoding="utf-8") as f:
        f.write(body)

# --- глобальні налаштування (один раз на курс) ---------------------------
st = GlobalSettings(course_name="Тактична медицина",
                    period_prefix="Заняття",
                    time_limit=20, attempts=2,
                    grading_method="highest", pass_percent=70,
                    shuffle_answers=True)

paths = [os.path.join("/tmp/mbz_raw", n) for n in FILES]
course, report = files_to_course(paths, st,
                                 course_fullname="М1 Тактична медицина",
                                 course_shortname="TACTMED_M1")
print(report)
assert len(course.sections) == 3, \
    f"очікувалося 3 секції, маємо {len(course.sections)}"

# --- збірка .mbz (tar.gz) --------------------------------------------------
builder = MbzBuilder(st, review_preset="standard")
data = builder.build(course)
out = "/tmp/mbz_raw/course_test.mbz"
with open(out, "wb") as f:
    f.write(data)
print(f"\n.mbz створено: {out} ({len(data)/1024:.1f} КБ)")

# --- сигнатура: має бути gzip (1f 8b), НЕ zip (PK) --------------------------
assert data[:2] == b"\x1f\x8b", "мbz має бути gzip, а не zip!"
assert data[:2] != b"PK", "помилка: zip-контейнер"
print("сигнатура gzip (1f 8b) ✔")

# --- валідація структури tar-архіву ------------------------------------------
z = tarfile.open(fileobj=io.BytesIO(gzip.decompress(data)))
names = z.getnames()
assert ".ARCHIVE_INDEX" in names, "немає .ARCHIVE_INDEX"

required_root = ["moodle_backup.xml", "questions.xml", "gradebook.xml",
                 "files.xml", "groups.xml", "outcomes.xml", "roles.xml",
                 "scales.xml", "badges.xml", "completion.xml",
                 "grade_history.xml", "users.xml",
                 "course/course.xml", "course/enrolments.xml",
                 "course/inforef.xml", "course/roles.xml"]
missing = [r for r in required_root if r not in names]
assert not missing, f"відсутні файли: {missing}"
# без кореневої обгортки
assert all(not n.startswith("course_test/") for n in names)

# секції: 1 загальна + 3 теми
sec_xmls = [n for n in names if n.startswith("sections/section_")
            and n.endswith("/section.xml")]
assert len(sec_xmls) == 4, f"секцій: {len(sec_xmls)}"
# активності: 3 тести
quiz_dirs = sorted(n for n in names if n.startswith("activities/quiz_")
                   and n.endswith("/quiz.xml"))
assert len(quiz_dirs) == 3, f"quiz.xml: {len(quiz_dirs)}"

# --- .ARCHIVE_INDEX: перший рядок-заголовок ---------------------------------
idx = z.extractfile(".ARCHIVE_INDEX").read().decode("utf-8")
assert idx.startswith("Moodle archive file index. Count:"), \
    "невірний заголовок .ARCHIVE_INDEX"
assert "moodle_backup.xml" in idx
print(".ARCHIVE_INDEX ✔")

# --- XML-валідність усіх файлів ----------------------------------------------
for n in names:
    if n.endswith(".xml"):
        ET.fromstring(z.extractfile(n).read().decode("utf-8"))
print("усі XML валідні ✔")

# --- перевірка структури XML (реальний формат Moodle 4.5) ----------------------
mb = z.extractfile("moodle_backup.xml").read().decode("utf-8")
assert "<original_course_contextid>10</original_course_contextid>" in mb
assert "<original_course_format>topics</original_course_format>" in mb
assert "<insubsection></insubsection>" in mb
assert "<parentcmid></parentcmid>" in mb

questions = z.extractfile("questions.xml").read().decode("utf-8")
# нова обгортка Moodle 4.x: question_bank_entries → question_version
assert "<question_bank_entries>" in questions
assert "<question_bank_entry id=" in questions
assert "<question_version>" in questions
assert "<question_versions id=" in questions
assert "<status>ready</status>" in questions
# 1 top + 3 категорії
assert questions.count("<question_category id=") == 4
# 4 питання загалом (2+1+1)
assert questions.count("<question id=") == 4
# правильна відповідь: по 1 на питання
assert questions.count('<fraction>1.0000000</fraction>') == 4
print("questions.xml: question_bank_entries ✔")

quiz1 = z.extractfile("activities/quiz_1/quiz.xml").read().decode("utf-8")
assert "<reviewattempt>69888</reviewattempt>" in quiz1
assert "<reviewcorrectness>4352</reviewcorrectness>" in quiz1
assert "<reviewmaxmarks>69888</reviewmaxmarks>" in quiz1   # нове поле 4.5
assert "<timelimit>1200</timelimit>" in quiz1              # 20 хв * 60
assert "<attempts_number>2</attempts_number>" in quiz1
assert "<grademethod>1</grademethod>" in quiz1             # highest
assert "<preferredbehaviour>deferredfeedback</preferredbehaviour>" in quiz1
assert quiz1.count("<question_instance id=") == 2          # 2 питання, тест 1
assert "<question_reference id=" in quiz1
assert "<questionbankentryid>" in quiz1          # фіксовані питання
assert "question_set_reference" not in quiz1    # НЕ випадкові
assert "<subplugin_quizaccess_seb_quiz>" in quiz1
assert "<overrides>" in quiz1 and "<attempts>" in quiz1
print("quiz.xml: question_instance + question_reference (fixed) + review flags ✔")

# module.xml: поля Moodle 4.5
mod1 = z.extractfile("activities/quiz_1/module.xml").read().decode("utf-8")
assert "<downloadcontent>1</downloadcontent>" in mod1
assert "<completiongradeitemnumber>$@NULL@$</completiongradeitemnumber>" in mod1
assert "<tags>" in mod1

# sequence у секції 2 (перша тема) має містити module id 1
sec2 = z.extractfile("sections/section_2/section.xml").read().decode("utf-8")
assert "<sequence>1</sequence>" in sec2
assert "<component>$@NULL@$</component>" in sec2
sec3 = z.extractfile("sections/section_3/section.xml").read().decode("utf-8")
assert "<sequence>2</sequence>" in sec3

# gradebook: 1 курс + 3 тести, нові поля
gb = z.extractfile("gradebook.xml").read().decode("utf-8")
assert gb.count("<grade_item id=") == 4
assert "<attributes>" in gb
assert "<decimals>$@NULL@$</decimals>" in gb
assert "<hidden>0</hidden>" in gb
print("gradebook.xml: attributes + decimals ✔")

# --- високорівневий конвеєр ---------------------------------------------------
out2 = "/tmp/mbz_raw/course_conv.mbz"
rep = build_mbz_from_files(paths, st, out2,
                           course_fullname="М1 Тактична медицина")
assert os.path.getsize(out2) > 2000
# перевірка, що і цей файл — gzip
with open(out2, "rb") as f:
    assert f.read(2) == b"\x1f\x8b"
print("\n=== УСІ ПЕРЕВІРКИ .mbz (tar.gz) ПРОЙДЕНО ===")
print(f"  course_test.mbz : {os.path.getsize(out)} байт")
print(f"  course_conv.mbz : {os.path.getsize(out2)} байт")
print(f"  файлів в архіві : {len(names)}")
