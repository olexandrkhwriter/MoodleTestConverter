# -*- coding: utf-8 -*-
"""Фінальна верифікація: core-конвертація + .mbz-конвеєр (без GUI)."""
import io, os, sys, zipfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 1. Конвертер (case24_newtem.txt) ===")
from converter_core import parse_file, to_gift, to_moodle_xml
qs = parse_file("tests_uni2/case24_newtem.txt")
print(f"   питань: {len(qs)}")
gift = to_gift(qs, "Категорія")
xml  = to_moodle_xml(qs, "Категорія")
assert "=" in gift or "~" in gift
ET.fromstring(xml)  # XML-валідність
print(f"   GIFT: {len(gift)} симв., XML: валідний ✔")

print("=== 2. Змішані формати -> .mbz ===")
from course_module import GlobalSettings
from mbz_module import build_mbz_from_files, files_to_course

os.makedirs("/tmp/fin", exist_ok=True)
open("/tmp/fin/01_a.txt","w",encoding="utf-8").write(
    "Питання 1?\nA. Варіант 1\nB. Варіант 2\nC. Варіант 3\nANSWER: B\n")
open("/tmp/fin/02_b.txt","w",encoding="utf-8").write(
    "Питання 2?\nA. Так\nB. Ні\nANSWER: A\n")

st = GlobalSettings(course_name="Фінальний тест", period_prefix="Тема",
                    time_limit=30, attempts=3, grading_method="average",
                    pass_percent=65, shuffle_answers=False)
course, rep = files_to_course(["/tmp/fin/01_a.txt","/tmp/fin/02_b.txt"],
                              st, course_fullname="Фінальний тест курсу")
print(rep)
out = "/tmp/fin/final_course.mbz"
rep = build_mbz_from_files(["/tmp/fin/01_a.txt","/tmp/fin/02_b.txt"], st,
                           out, course_fullname="Фінальний тест курсу")
z = zipfile.ZipFile(io.BytesIO(open(out,"rb").read()))
names = z.namelist()
assert "moodle_backup.xml" in names
assert "questions.xml" in names
assert len([n for n in names if n.startswith("activities/quiz_") and n.endswith("quiz.xml")]) == 2
for n in names:
    if n.endswith(".xml"):
        ET.fromstring(z.read(n).decode("utf-8"))
# перевірка глобальних налаштувань в .mbz
q1 = z.read("activities/quiz_1/quiz.xml").decode("utf-8")
assert "<timelimit>1800</timelimit>" in q1          # 30 хв
assert "<attempts_number>3</attempts_number>" in q1
assert "<grademethod>2</grademethod>" in q1          # average
assert "<shuffleanswers>0</shuffleanswers>" in q1
print(f"   .mbz: {len(names)} файлів, усі XML валідні ✔")
print(f"   налаштування застосовано (30хв/3 спроби/average/no-shuffle) ✔")

print("\n=== УСІ ПЕРЕВІРКИ ПРОЙДЕНО ===")
