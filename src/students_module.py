# -*- coding: utf-8 -*-
"""
Модуль створення списків студентів для додавання до груп Moodle.
Підтримує введення «Прізвище Ім'я» (можна з по-батькові) або
«Прізвище, Ім'я, email», валідацію, генерацію username та
експорт у формати Moodle (CSV для завантаження користувачів,
CSV для зарахування до когорт/груп, XLSX).
"""

import re
import csv
import io


# Транслітерація українських літер для username
_TRANS = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "i",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia", "'": "", "’": "",
}


def transliterate(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(_TRANS.get(ch, ch))
    return "".join(out)


class StudentError(ValueError):
    pass


def parse_students(text: str):
    """
    Parse a block of lines, one student per line:
      'Прізвище Ім'я' | 'Прізвище Ім'я По-батькові' | 'Прізвище, Ім'я'
      | 'Прізвище, Ім'я, email@...' | 'Прізвище Ім'я email@...'
    Returns list of dicts: lastname, firstname, email, username, errors.
    """
    students = []
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue
        email = ""
        m = re.search(r"[\w.\-]+@[\w\-]+(\.[\w\-]+)+", line)
        if m:
            email = m.group(0)
            line = (line[:m.start()] + line[m.end():]).strip(" ,;")
        if "," in line:
            parts = [p.strip() for p in line.split(",") if p.strip()]
        else:
            parts = [p.strip() for p in re.split(r"\s+", line) if p.strip()]
        if len(parts) < 2:
            students.append({"lastname": line, "firstname": "", "email": email,
                             "username": "", "error":
                             f"рядок {ln}: потрібно щонайменше прізвище та ім'я"})
            continue
        lastname, firstname = parts[0], parts[1]
        username = transliterate(lastname + "." + firstname)
        username = re.sub(r"[^a-z0-9.\-]", "", username)
        err = ""
        if not re.fullmatch(r"[А-Яа-яЇїІіЄєҐґ'’\-]+", lastname or ""):
            err = f"рядок {ln}: підозріле прізвище"
        students.append({"lastname": lastname, "firstname": firstname,
                         "email": email, "username": username, "error": err})
    return students


def students_to_moodle_csv(students, course1="", group1="",
                           password="ChangeMe123!") -> str:
    """
    Moodle 'Upload users' CSV format:
    username,password,firstname,lastname,email,course1,group1
    """
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["username", "password", "firstname", "lastname", "email",
                "course1", "group1"])
    for i, s in enumerate(students, 1):
        if s.get("error") and not s["firstname"]:
            continue
        email = s["email"] or f'{s["username"]}@example.com'
        w.writerow([s["username"], password, s["firstname"], s["lastname"],
                    email, course1, group1])
    return buf.getvalue()


def students_to_cohort_csv(students, cohort="", password="ChangeMe123!") -> str:
    """CSV for bulk cohort enrolment: username,password,...,cohort1"""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["username", "password", "firstname", "lastname", "email",
                "cohort1"])
    for s in students:
        if s.get("error") and not s["firstname"]:
            continue
        email = s["email"] or f'{s["username"]}@example.com'
        w.writerow([s["username"], password, s["firstname"], s["lastname"],
                    email, cohort])
    return buf.getvalue()


def students_to_xlsx_rows(students):
    rows = [["Прізвище", "Ім'я", "Username", "Email"]]
    for s in students:
        rows.append([s["lastname"], s["firstname"], s["username"],
                     s["email"] or f'{s["username"]}@example.com'])
    return rows
