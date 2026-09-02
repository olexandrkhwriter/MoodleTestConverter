# -*- coding: utf-8 -*-
"""
Модуль генерації готового курсу Moodle (MoodleCourseGenerator).

Приймає пакет "сирих" текстових файлів із тестами (формат Aiken),
застосовує ЄДИНІ глобальні налаштування тестування (задаються 1 раз на
весь курс) та генерує єдиний ієрархічний Moodle XML, готовий до імпорту
в банк питань Moodle.

Структура категорій:  $course$/top/{courseName}/{periodPrefix} {N} - {Назва}
У <info> кожної категорії додаються глобальні налаштування тесту.
"""

from __future__ import annotations

import os
import re
import html
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Модель даних
# ---------------------------------------------------------------------------

@dataclass
class GlobalSettings:
    """Глобальні налаштування тестування — задаються ОДИН раз на курс."""
    course_name: str = "Курс"
    period_prefix: str = "Заняття"
    time_limit: int = 0            # хвилини; 0 = без обмежень
    attempts: int = 0              # 0 = необмежено
    grading_method: str = "highest"   # highest | average | last | first
    pass_percent: int = 60
    shuffle_answers: bool = True
    random_questions: int = 0    # 0 = усі питання фіксовані (question_reference);
                                 # N>0 = тест бере N ВИПАДКОВИХ питань із своєї
                                 # категорії (question_set_reference)

    def info_text(self) -> str:
        grading_ua = {"highest": "найкраща спроба",
                      "average": "середнє арифметичне",
                      "last": "остання спроба",
                      "first": "перша спроба"}.get(self.grading_method,
                                                   self.grading_method)
        tl = ("без обмеження часу" if self.time_limit == 0
              else f"{self.time_limit} хв")
        at = ("необмежено" if self.attempts == 0 else str(self.attempts))
        return (f"Тривалість: {tl}; Спроб: {at}; "
                f"Оцінювання: {grading_ua}; Прохідний бал: {self.pass_percent}%")


@dataclass
class AikenQuestion:
    text: str
    options: List[str] = field(default_factory=list)   # [A..E]
    correct_index: int = -1                            # 0-based


@dataclass
class FileReport:
    filename: str
    questions: int = 0
    skipped: bool = False
    warning: str = ""


# ---------------------------------------------------------------------------
# Генератор курсу
# ---------------------------------------------------------------------------

class MoodleCourseGenerator:
    """Генерує єдиний ієрархічний Moodle XML з пакету Aiken-файлів."""

    def __init__(self, settings: GlobalSettings):
        self.settings = settings
        self.reports: List[FileReport] = []

    # ---------------------------------------------------------- helpers
    @staticmethod
    def _natural_key(name: str):
        """Natural sorting: 'Тема 2' < 'Тема 10'."""
        return [int(t) if t.isdigit() else t.lower()
                for t in re.split(r"(\d+)", name)]

    @staticmethod
    def _clean_filename(name: str) -> str:
        """Прибрати розширення та службові префікси-цифри."""
        base = os.path.splitext(os.path.basename(name))[0]
        base = re.sub(r"^\d+[_\-\. ]*", "", base).strip()
        base = base.replace("_", " ").strip()
        return base or os.path.splitext(os.path.basename(name))[0]

    @staticmethod
    def _esc(text: str) -> str:
        return html.escape(text, quote=True)

    # ---------------------------------------------------------- parsing
    _OPTION_RE = re.compile(
        r"^\s*([A-ZА-ЯЇІЄҐa-zа-яїієґ])\s*[\.\)\:]\s*(.+?)\s*$")
    _ANSWER_RE = re.compile(
        r"^\s*(?:ANSWER|ANS|ВІДПОВІДЬ)\s*[:：]?\s*([A-ZА-ЯЇІЄҐa-zа-яїієґ])\s*"
        r"\.?\s*$", re.IGNORECASE)

    def parse_aiken(self, raw: str) -> List[AikenQuestion]:
        """Парсить сирий Aiken-текст у список питань.
        Стійкий до 'Answer:', 'ANSWER :', варіантів 'A)' замість 'A.'."""
        # нормалізація: \r\n → \n, прибрати зайві пробіли
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        raw = re.sub(r"[ \t]+", " ", raw)
        lines = [l.rstrip() for l in raw.split("\n")]

        questions: List[AikenQuestion] = []
        cur_text: List[str] = []
        cur_opts: List[Tuple[str, str]] = []

        def flush():
            if not cur_opts:
                cur_text.clear()
                return
            # знайти правильну (мітка ANSWER обробляється у циклі)
            if cur_opts:
                letters = [l for l, _ in cur_opts]
                q = AikenQuestion(text=" ".join(cur_text).strip(),
                                  options=[t for _, t in cur_opts])
                questions.append(q)
            cur_text.clear()
            cur_opts.clear()

        pending_answer_letter: Optional[str] = None
        for line in lines:
            if not line.strip():
                # порожній рядок — роздільник питань (якщо є варіанти)
                if cur_opts:
                    flush()
                continue
            am = self._ANSWER_RE.match(line)
            if am:
                letter = am.group(1).upper()
                # позначити правильний варіант
                if cur_opts:
                    letters = [l.upper() for l, _ in cur_opts]
                    if letter in letters:
                        idx = letters.index(letter)
                        q = AikenQuestion(
                            text=" ".join(cur_text).strip(),
                            options=[t for _, t in cur_opts],
                            correct_index=idx)
                        questions.append(q)
                        cur_text.clear()
                        cur_opts.clear()
                continue
            om = self._OPTION_RE.match(line)
            if om:
                cur_opts.append((om.group(1).upper(), om.group(2).strip()))
                continue
            # інакше — частина тексту питання (можливо багаторядкова)
            if not cur_opts:
                cur_text.append(line.strip())
            else:
                # продовження останнього варіанта
                cur_opts[-1] = (cur_opts[-1][0],
                                cur_opts[-1][1] + " " + line.strip())
        flush()
        # відфільтрувати питання без правильної відповіді
        return [q for q in questions if q.correct_index >= 0
                and len(q.options) >= 2 and q.text]

    # ---------------------------------------------------------- build
    def generate(self, file_paths: List[str],
                 topic_overrides: Optional[List[str]] = None
                 ) -> Tuple[str, str]:
        """
        Обробляє пакет файлів і повертає (xml_string, report_text).
        topic_overrides — необов'язковий список назв тем (1 рядок =
        1 заняття); якщо задано, підставляється в назву категорії
        замість назви файлу.
        """
        # 1) natural sorting
        paths = sorted(file_paths,
                       key=lambda p: self._natural_key(os.path.basename(p)))
        self.reports = []

        out = ['<?xml version="1.0" encoding="UTF-8"?>', "<quiz>"]
        info = self.settings.info_text()

        for i, path in enumerate(paths, 1):
            fname = os.path.basename(path)
            rep = FileReport(filename=fname)
            try:
                with open(path, "rb") as f:
                    raw = f.read()
                # надійне розпізнавання кодування (UTF-8 / UTF-8-BOM /
                # Windows-1251) — те саме, що й у ядрі конвертера
                try:
                    from converter_core import decode_bytes
                    text = decode_bytes(raw)
                except ImportError:
                    for enc in ("utf-8-sig", "utf-8", "cp1251"):
                        try:
                            text = raw.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        text = raw.decode("utf-8", errors="replace")
                questions = self.parse_aiken(text)
            except Exception as e:
                rep.skipped = True
                rep.warning = f"помилка читання: {e}"
                self.reports.append(rep)
                continue

            if not questions:
                rep.skipped = True
                rep.warning = "валідних питань не знайдено"
                self.reports.append(rep)
                continue

            rep.questions = len(questions)
            self.reports.append(rep)

            # назва заняття: зі списку тем (за порядком) або з файлу
            if topic_overrides and (i - 1) < len(topic_overrides) \
                    and topic_overrides[i - 1]:
                clean = topic_overrides[i - 1]
            else:
                clean = self._clean_filename(fname)
            category = (f"$course$/top/{self.settings.course_name}/"
                        f"{self.settings.period_prefix} {i} - {clean}")

            # блок категорії
            out.append('  <question type="category">')
            out.append("    <category>")
            out.append(f"      <text>{self._esc(category)}</text>")
            out.append("    </category>")
            out.append('    <info format="moodle_auto_format">')
            out.append(f"      <text>{self._esc(info)}</text>")
            out.append("    </info>")
            out.append("  </question>")

            # питання
            shuffle = "true" if self.settings.shuffle_answers else "false"
            for j, q in enumerate(questions, 1):
                name = (q.text[:57] + "...") if len(q.text) > 60 else q.text
                qname = f"{self.settings.period_prefix} {i} — Питання {j}"
                out.append('  <question type="multichoice">')
                out.append(f"    <name><text>{self._esc(qname)}</text></name>")
                out.append('    <questiontext format="html">')
                out.append(f"      <text><![CDATA[{q.text}]]></text>")
                out.append("    </questiontext>")
                out.append("    <defaultgrade>1.0</defaultgrade>")
                out.append("    <single>true</single>")
                out.append(f"    <shuffleanswers>{shuffle}</shuffleanswers>")
                out.append("    <answernumbering>abc</answernumbering>")
                for k, opt in enumerate(q.options):
                    frac = "100" if k == q.correct_index else "0"
                    out.append(f'    <answer fraction="{frac}" format="html">')
                    out.append(f"      <text><![CDATA[{opt}]]></text>")
                    out.append("    </answer>")
                out.append("  </question>")

        out.append("</quiz>")
        xml_string = "\n".join(out) + "\n"
        return xml_string, self._build_report()

    def _build_report(self) -> str:
        ok = sum(1 for r in self.reports if not r.skipped)
        total_q = sum(r.questions for r in self.reports)
        lines = [f"Оброблено файлів: {ok} з {len(self.reports)}",
                 f"Всього питань: {total_q}", ""]
        for r in self.reports:
            if r.skipped:
                lines.append(f"  ⚠ {r.filename}: пропущено ({r.warning})")
            else:
                lines.append(f"  ✔ {r.filename}: {r.questions} питань")
        return "\n".join(lines)
