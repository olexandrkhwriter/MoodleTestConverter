# -*- coding: utf-8 -*-
"""
Генератор повної резервної копії курсу Moodle у форматі .mbz
(Moodle Backup Format, перевірено на реальному бекапі Moodle 4.5.2).

ВАЖЛИВО: реальний .mbz — це TAR-архів, стиснений GZIP (tar.gz), із
службовим індексом .ARCHIVE_INDEX у корені. НЕ zip!

Вхід: набір "сирих" файлів (txt/docx/doc/csv/xlsx/html — усе, що читає
converter_core, або Aiken через course_module), згрупованих у секції
(теми/заняття). Глобальні налаштування тестування задаються ОДИН раз
на весь курс.

Структура контейнера:
  .ARCHIVE_INDEX, moodle_backup.xml, questions.xml, gradebook.xml,
  files.xml, groups.xml, outcomes.xml, roles.xml, scales.xml,
  badges.xml, completion.xml, grade_history.xml, users.xml,
  course/{course,enrolments,inforef,roles,...}.xml,
  sections/section_{N}/{section,inforef}.xml,
  activities/quiz_{N}/{module,quiz,inforef,grades,roles,...}.xml

Відповідає документу docs/MOODLE_MBZ_SPECIFICATION.md.
"""

from __future__ import annotations

import gzip
import html
import io
import os
import re
import tarfile
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from course_module import AikenQuestion, GlobalSettings, MoodleCourseGenerator


# ---------------------------------------------------------------------------
# Модель даних курсу
# ---------------------------------------------------------------------------

@dataclass
class CourseQuiz:
    """Один тест (Quiz) усередині секції."""
    name: str
    intro: str = ""
    questions: List[AikenQuestion] = field(default_factory=list)
    category_name: str = ""                      # категорія банку питань


@dataclass
class CourseSection:
    """Одна секція (тема/заняття) курсу з її тестами."""
    title: str                                   # назва секції
    summary: str = ""                            # опис секції
    quizzes: List[CourseQuiz] = field(default_factory=list)


@dataclass
class MbzCourse:
    """Опис курсу для пакування в .mbz."""
    fullname: str
    shortname: str
    summary: str = ""
    sections: List[CourseSection] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Налаштування поведінки тесту (Review flags тощо)
# ---------------------------------------------------------------------------

# Бітові маски Review Options (див. специфікацію §5.1).
# Реальний бекап Moodle 4.5: standard = reviewattempt 69888 / решта 4352,
# плюс обов'язкове reviewmaxmarks 69888.
REVIEW_PRESETS = {
    "standard": dict(reviewattempt=69888, reviewcorrectness=4352,
                     reviewmaxmarks=69888, reviewmarks=4352,
                     reviewspecificfeedback=4352, reviewgeneralfeedback=4352,
                     reviewrightanswer=4352, reviewoverallfeedback=4352),
    "strict":   dict(reviewattempt=69888, reviewcorrectness=0,
                     reviewmaxmarks=69888, reviewmarks=4352,
                     reviewspecificfeedback=0, reviewgeneralfeedback=0,
                     reviewrightanswer=0, reviewoverallfeedback=4352),
    "full":     dict(reviewattempt=69904, reviewcorrectness=69904,
                     reviewmaxmarks=69904, reviewmarks=69904,
                     reviewspecificfeedback=69904, reviewgeneralfeedback=69904,
                     reviewrightanswer=69904, reviewoverallfeedback=69904),
}

GRADEMETHOD_CODES = {"highest": 1, "average": 2, "first": 3, "last": 4}


# ---------------------------------------------------------------------------
# Генератор .mbz
# ---------------------------------------------------------------------------

class MbzBuilder:
    """Будує tar.gz-архів .mbz з повним набором XML за специфікацією."""

    def __init__(self, settings: GlobalSettings,
                 review_preset: str = "standard",
                 behaviour: str = "deferredfeedback",
                 questions_per_page: int = 1,
                 navmethod: str = "free"):
        self.settings = settings
        self.review = REVIEW_PRESETS.get(review_preset,
                                         REVIEW_PRESETS["standard"])
        self.behaviour = behaviour
        self.questions_per_page = questions_per_page
        self.navmethod = navmethod
        self.now = int(time.time())

        # ID-лічильники (див. §3 специфікації)
        self._cat_id = 1          # 1 = top (категорія курсу)
        self._question_id = 1000
        self._answer_id = 10000
        self._module_id = 0
        self._section_db_id = 0   # 1 = загальна секція (number 0)
        self._grade_item_id = 1   # 1 = підсумок курсу

    # ---------------------------------------------------------- helpers
    @staticmethod
    def _esc(text: str) -> str:
        return html.escape(text or "", quote=True)

    def _next_cat(self) -> int:
        self._cat_id += 1
        return self._cat_id

    def _next_question(self) -> int:
        self._question_id += 1
        return self._question_id

    def _next_answer(self) -> int:
        self._answer_id += 1
        return self._answer_id

    # ---------------------------------------------------------- build API
    def build(self, course: MbzCourse) -> bytes:
        """Повертає вміст .mbz (bytes tar.gz, готовий до запису на диск)."""
        # --- попередня нумерація: призначити ID всім сутностям
        sections = [CourseSection(title="Загальне")] + list(course.sections)
        section_ids = {}          # index у sections -> db id
        module_map = []           # (module_id, section_index, quiz)
        for si, sec in enumerate(sections):
            self._section_db_id += 1
            section_ids[si] = self._section_db_id
            for qz in sec.quizzes:
                self._module_id += 1
                module_map.append((self._module_id, si, qz))

        # категорії питань: 1=top (курс), далі по одній на quiz
        cat_for_quiz = {}
        for module_id, si, qz in module_map:
            cat_for_quiz[module_id] = self._next_cat()

        # питання: присвоїти ID
        qid_map = {}              # (module_id, id(question obj)) -> q_id
        for module_id, si, qz in module_map:
            for q in qz.questions:
                qid_map[(module_id, id(q))] = self._next_question()

        # зібрати всі файли у словник шлях -> bytes
        files = {}
        files["moodle_backup.xml"] = self._xml_moodle_backup(
            course, sections, section_ids, module_map)
        files["questions.xml"] = self._xml_questions(
            module_map, cat_for_quiz, qid_map)
        files["gradebook.xml"] = self._xml_gradebook(module_map)
        files["files.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                              '<files>\n</files>\n')
        files["groups.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                               '<groups>\n  <groupcustomfields>\n'
                               '  </groupcustomfields>\n  <groupings>\n'
                               '  </groupings>\n</groups>\n')
        files["outcomes.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                                 '<outcomes_definition>\n'
                                 '</outcomes_definition>\n')
        files["roles.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                              '<roles_definition>\n</roles_definition>\n')
        files["scales.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                               '<scales_definition>\n</scales_definition>\n')
        files["badges.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                               '<badges>\n</badges>\n')
        files["completion.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                                   '<course_completion>\n'
                                   '</course_completion>\n')
        files["grade_history.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<grade_history>\n'
            '  <grade_grades>\n  </grade_grades>\n</grade_history>\n')
        files["users.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                              '<users>\n</users>\n')
        files["moodle_backup.log"] = ""

        # course/
        files["course/course.xml"] = self._xml_course(course, sections)
        files["course/enrolments.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<enrolments>\n'
            '  <enrols>\n  </enrols>\n</enrolments>\n')
        files["course/inforef.xml"] = self._xml_course_inforef(cat_for_quiz)
        files["course/roles.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<roles>\n'
            '  <role_overrides>\n  </role_overrides>\n'
            '  <role_assignments>\n  </role_assignments>\n</roles>\n')
        files["course/filters.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<filters>\n'
            '  <filter_actives>\n  </filter_actives>\n'
            '  <filter_configs>\n  </filter_configs>\n</filters>\n')
        files["course/comments.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<comments>\n'
            '</comments>\n')
        files["course/calendar.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<events>\n</events>\n')
        files["course/contentbank.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n<contents>\n'
            '</contents>\n')
        files["course/completiondefaults.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<course_completion_defaults>\n</course_completion_defaults>\n')
        files["course/competencies.xml"] = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<course_competencies>\n</course_competencies>\n')

        # sections/
        for si, sec in enumerate(sections):
            db_id = section_ids[si]
            mods = [m for m, s, _ in module_map if s == si]
            files[f"sections/section_{db_id}/section.xml"] = \
                self._xml_section(db_id, si, sec, mods)
            files[f"sections/section_{db_id}/inforef.xml"] = \
                self._xml_section_inforef()

        # activities/
        for module_id, si, qz in module_map:
            cat_id = cat_for_quiz[module_id]
            qids = [qid_map[(module_id, id(q))] for q in qz.questions]
            d = f"activities/quiz_{module_id}"
            files[f"{d}/module.xml"] = self._xml_module(
                module_id, section_ids[si], si)
            files[f"{d}/quiz.xml"] = self._xml_quiz(
                module_id, qz, qids, cat_id)
            files[f"{d}/inforef.xml"] = self._xml_quiz_inforef(cat_id, qids)
            self._grade_item_id += 1
            files[f"{d}/grades.xml"] = self._xml_grades(
                module_id, qz, self._grade_item_id)
            files[f"{d}/roles.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<roles>\n'
                '  <role_overrides>\n  </role_overrides>\n'
                '  <role_assignments>\n  </role_assignments>\n</roles>\n')
            files[f"{d}/filters.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<filters>\n'
                '  <filter_actives>\n  </filter_actives>\n'
                '  <filter_configs>\n  </filter_configs>\n</filters>\n')
            files[f"{d}/grade_history.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<grade_history>\n'
                '  <grade_grades>\n  </grade_grades>\n</grade_history>\n')
            files[f"{d}/completion.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<completions>\n'
                '</completions>\n')
            files[f"{d}/comments.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<comments>\n'
                '</comments>\n')
            files[f"{d}/calendar.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<events>\n'
                '</events>\n')
            files[f"{d}/xapistate.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n<xapistates>\n'
                '</xapistates>\n')
            files[f"{d}/competencies.xml"] = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<course_module_competencies>\n'
                '</course_module_competencies>\n')

        return self._pack_tar_gz(files)

    # ---------------------------------------------------------- packing
    def _pack_tar_gz(self, files: dict) -> bytes:
        """Пакує словник файлів у tar.gz із .ARCHIVE_INDEX (формат Moodle)."""
        # .ARCHIVE_INDEX: перший файл, таб-розділений індекс
        lines = [f"Moodle archive file index. Count: {len(files)}"]
        for path in sorted(files):
            lines.append(f"{path}\tf\t{len(files[path].encode('utf-8'))}"
                         f"\t{self.now}")
        index = "\n".join(lines) + "\n"

        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w",
                              format=tarfile.USTAR_FORMAT) as tar:
                # .ARCHIVE_INDEX — першим
                data = index.encode("utf-8")
                ti = tarfile.TarInfo(".ARCHIVE_INDEX")
                ti.size = len(data)
                ti.mtime = self.now
                ti.mode = 0o644
                tar.addfile(ti, io.BytesIO(data))
                # директорії
                dirs = sorted({os.path.dirname(p) for p in files
                               if "/" in p} | {"course", "sections",
                                               "activities"})
                for d in dirs:
                    di = tarfile.TarInfo(d)
                    di.type = tarfile.DIRTYPE
                    di.mtime = self.now
                    di.mode = 0o755
                    tar.addfile(di)
                # файли
                for path in sorted(files):
                    data = files[path].encode("utf-8")
                    ti = tarfile.TarInfo(path)
                    ti.size = len(data)
                    ti.mtime = self.now
                    ti.mode = 0o644
                    tar.addfile(ti, io.BytesIO(data))
        return buf.getvalue()

    # ---------------------------------------------------------- XML: root
    def _xml_moodle_backup(self, course, sections, section_ids,
                           module_map) -> str:
        ts = self.now
        acts, secs = [], []
        for module_id, si, qz in module_map:
            acts.append(
                "        <activity>\n"
                f"          <moduleid>{module_id}</moduleid>\n"
                f"          <sectionid>{section_ids[si]}</sectionid>\n"
                "          <modulename>quiz</modulename>\n"
                f"          <title>{self._esc(qz.name)}</title>\n"
                f"          <directory>activities/quiz_{module_id}"
                "</directory>\n"
                "          <insubsection></insubsection>\n"
                "        </activity>")
        for si, sec in enumerate(sections):
            db_id = section_ids[si]
            secs.append(
                "        <section>\n"
                f"          <sectionid>{db_id}</sectionid>\n"
                f"          <title>{self._esc(sec.title)}</title>\n"
                f"          <directory>sections/section_{db_id}</directory>\n"
                "          <parentcmid></parentcmid>\n"
                "          <modname></modname>\n"
                "        </section>")

        settings = [
            ('root', 'filename', 'backup.mbz'),
            ('root', 'users', '0'),
            ('root', 'anonymize', '0'),
            ('root', 'role_assignments', '0'),
            ('root', 'activities', '1'),
            ('root', 'blocks', '0'),
            ('root', 'files', '0'),
            ('root', 'filters', '0'),
            ('root', 'comments', '0'),
            ('root', 'badges', '0'),
            ('root', 'calendarevents', '0'),
            ('root', 'userscompletion', '0'),
            ('root', 'logs', '0'),
            ('root', 'grade_histories', '0'),
            ('root', 'questionbank', '1'),
            ('root', 'groups', '0'),
            ('root', 'competencies', '0'),
            ('root', 'customfield', '0'),
        ]
        for si in range(len(sections)):
            db_id = section_ids[si]
            settings.append(('section', f'section_{db_id}_included', '1'))
            settings.append(('section', f'section_{db_id}_userinfo', '0'))
        for module_id, si, qz in module_map:
            settings.append(('activity', f'quiz_{module_id}_included', '1'))
            settings.append(('activity', f'quiz_{module_id}_userinfo', '0'))

        set_xml = []
        for level, name, value in settings:
            if level == 'root':
                set_xml.append(
                    f'      <setting><level>root</level><name>{name}</name>'
                    f'<value>{value}</value></setting>')
            elif level == 'section':
                db_id = name.split("_")[1]
                set_xml.append(
                    f'      <setting><level>section</level>'
                    f'<section>section_{db_id}</section>'
                    f'<name>{name}</name><value>{value}</value></setting>')
            else:
                mid = name.split("_")[1]
                set_xml.append(
                    f'      <setting><level>activity</level>'
                    f'<activity>quiz_{mid}</activity>'
                    f'<name>{name}</name><value>{value}</value></setting>')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<moodle_backup>
  <information>
    <name>backup.mbz</name>
    <moodle_version>2024100702</moodle_version>
    <moodle_release>4.5.2 (Build: 20250210)</moodle_release>
    <backup_version>2024100700</backup_version>
    <backup_release>4.5</backup_release>
    <backup_date>{ts}</backup_date>
    <mnet_remoteusers>0</mnet_remoteusers>
    <include_files>0</include_files>
    <include_file_references_to_external_content>0</include_file_references_to_external_content>
    <original_wwwroot>http://localhost</original_wwwroot>
    <original_site_identifier_hash>mbzhash</original_site_identifier_hash>
    <original_course_id>2</original_course_id>
    <original_course_format>topics</original_course_format>
    <original_course_fullname>{self._esc(course.fullname)}</original_course_fullname>
    <original_course_shortname>{self._esc(course.shortname)}</original_course_shortname>
    <original_course_startdate>{ts}</original_course_startdate>
    <original_course_enddate>0</original_course_enddate>
    <original_course_contextid>10</original_course_contextid>
    <original_system_contextid>1</original_system_contextid>
    <details>
      <detail backup_id="mbz_{ts}">
        <type>course</type>
        <format>moodle2</format>
        <interactive>1</interactive>
        <mode>10</mode>
        <execution>1</execution>
        <executiontime>0</executiontime>
      </detail>
    </details>
    <contents>
      <activities>
{chr(10).join(acts)}
      </activities>
      <sections>
{chr(10).join(secs)}
      </sections>
      <course>
        <courseid>2</courseid>
        <title>{self._esc(course.fullname)}</title>
        <directory>course</directory>
      </course>
    </contents>
    <settings>
{chr(10).join(set_xml)}
    </settings>
  </information>
</moodle_backup>
'''

    # ---------------------------------------------------------- XML: course
    def _xml_course(self, course, sections) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<course id="2" contextid="10">
  <shortname>{self._esc(course.shortname)}</shortname>
  <fullname>{self._esc(course.fullname)}</fullname>
  <idnumber></idnumber>
  <summary>{self._esc("<p>" + (course.summary or "") + "</p>")}</summary>
  <summaryformat>1</summaryformat>
  <format>topics</format>
  <showgrades>1</showgrades>
  <newsitems>5</newsitems>
  <startdate>{self.now}</startdate>
  <enddate>0</enddate>
  <marker>0</marker>
  <maxbytes>0</maxbytes>
  <legacyfiles>0</legacyfiles>
  <showreports>0</showreports>
  <visible>1</visible>
  <groupmode>0</groupmode>
  <groupmodeforce>0</groupmodeforce>
  <defaultgroupingid>0</defaultgroupingid>
  <lang></lang>
  <theme></theme>
  <timecreated>{self.now}</timecreated>
  <timemodified>{self.now}</timemodified>
  <requested>0</requested>
  <showactivitydates>1</showactivitydates>
  <showcompletionconditions>1</showcompletionconditions>
  <pdfexportfont>$@NULL@$</pdfexportfont>
  <enablecompletion>1</enablecompletion>
  <completionnotify>0</completionnotify>
  <category id="1">
    <name>Miscellaneous</name>
    <description></description>
  </category>
  <tags>
  </tags>
  <customfields>
  </customfields>
  <courseformatoptions>
    <courseformatoption>
      <format>topics</format>
      <sectionid>0</sectionid>
      <name>hiddensections</name>
      <value>0</value>
    </courseformatoption>
    <courseformatoption>
      <format>topics</format>
      <sectionid>0</sectionid>
      <name>coursedisplay</name>
      <value>0</value>
    </courseformatoption>
  </courseformatoptions>
</course>
'''

    def _xml_course_inforef(self, cat_for_quiz) -> str:
        cats = ["      <question_category>\n        <id>1</id>\n"
                "      </question_category>"]
        for cid in sorted(set(cat_for_quiz.values())):
            cats.append(f"      <question_category>\n        <id>{cid}</id>"
                        f"\n      </question_category>")
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<inforef>\n'
                '  <question_categoryref>\n' + "\n".join(cats) +
                "\n  </question_categoryref>\n</inforef>\n")

    # ---------------------------------------------------------- XML: sections
    def _xml_section(self, db_id, number, sec, module_ids) -> str:
        seq = ",".join(str(m) for m in module_ids)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<section id="{db_id}">
  <number>{number}</number>
  <name>{self._esc(sec.title)}</name>
  <summary>{self._esc("<p>" + (sec.summary or "") + "</p>")}</summary>
  <summaryformat>1</summaryformat>
  <sequence>{seq}</sequence>
  <visible>1</visible>
  <availabilityjson>$@NULL@$</availabilityjson>
  <component>$@NULL@$</component>
  <itemid>$@NULL@$</itemid>
  <timemodified>{self.now}</timemodified>
</section>
'''

    @staticmethod
    def _xml_section_inforef() -> str:
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<inforef>\n'
                '</inforef>\n')

    # ---------------------------------------------------------- XML: questions
    def _xml_questions(self, module_map, cat_for_quiz, qid_map) -> str:
        ts = self.now
        parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<question_categories>',
                 '''  <question_category id="1">
    <name>top</name>
    <contextid>10</contextid>
    <contextlevel>50</contextlevel>
    <contextinstanceid>2</contextinstanceid>
    <info></info>
    <infoformat>0</infoformat>
    <stamp>localhost+cat+top</stamp>
    <parent>0</parent>
    <sortorder>0</sortorder>
    <idnumber>$@NULL@$</idnumber>
    <question_bank_entries>
    </question_bank_entries>
  </question_category>''']

        shuffle = "1" if self.settings.shuffle_answers else "0"
        for sort_n, (module_id, si, qz) in enumerate(module_map, 1):
            cat_id = cat_for_quiz[module_id]
            cat_name = qz.category_name or qz.name
            entries = []
            for q in qz.questions:
                qid = qid_map[(module_id, id(q))]
                answers = []
                for opt_i, opt in enumerate(q.options):
                    aid = self._next_answer()
                    frac = ("1.0000000" if opt_i == q.correct_index
                            else "0.0000000")
                    answers.append(f'''                    <answer id="{aid}">
                      <answertext>{self._esc(opt)}</answertext>
                      <answerformat>1</answerformat>
                      <fraction>{frac}</fraction>
                      <feedback></feedback>
                      <feedbackformat>1</feedbackformat>
                    </answer>''')
                qname = q.text[:60] + (" ..." if len(q.text) > 60 else "")
                entries.append(f'''      <question_bank_entry id="{qid}">
        <questioncategoryid>{cat_id}</questioncategoryid>
        <idnumber>$@NULL@$</idnumber>
        <ownerid>2</ownerid>
        <question_version>
          <question_versions id="{qid}">
            <version>1</version>
            <status>ready</status>
            <questions>
              <question id="{qid}">
                <parent>0</parent>
                <name>{self._esc(qname)}</name>
                <questiontext>{self._esc(q.text)}</questiontext>
                <questiontextformat>1</questiontextformat>
                <generalfeedback></generalfeedback>
                <generalfeedbackformat>1</generalfeedbackformat>
                <defaultmark>1.0000000</defaultmark>
                <penalty>0.3333333</penalty>
                <qtype>multichoice</qtype>
                <length>1</length>
                <stamp>localhost+q+{qid}</stamp>
                <timecreated>{ts}</timecreated>
                <timemodified>{ts}</timemodified>
                <createdby>2</createdby>
                <modifiedby>2</modifiedby>
                <plugin_qtype_multichoice_question>
                  <answers>
{chr(10).join(answers)}
                  </answers>
                  <multichoice id="{qid}">
                    <layout>0</layout>
                    <single>1</single>
                    <shuffleanswers>{shuffle}</shuffleanswers>
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
      </question_bank_entry>''')

            parts.append(f'''  <question_category id="{cat_id}">
    <name>{self._esc(cat_name)}</name>
    <contextid>10</contextid>
    <contextlevel>50</contextlevel>
    <contextinstanceid>2</contextinstanceid>
    <info></info>
    <infoformat>1</infoformat>
    <stamp>localhost+cat+{cat_id}</stamp>
    <parent>1</parent>
    <sortorder>{sort_n * 1000}</sortorder>
    <idnumber>$@NULL@$</idnumber>
    <question_bank_entries>
{chr(10).join(entries)}
    </question_bank_entries>
  </question_category>''')

        parts.append('</question_categories>')
        return "\n".join(parts) + "\n"

    # ---------------------------------------------------------- XML: activity
    def _xml_module(self, module_id, section_db_id, section_number) -> str:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<module id="{module_id}" version="2024100700">
  <modulename>quiz</modulename>
  <sectionid>{section_db_id}</sectionid>
  <sectionnumber>{section_number}</sectionnumber>
  <idnumber></idnumber>
  <added>{self.now}</added>
  <score>0</score>
  <indent>0</indent>
  <visible>1</visible>
  <visibleoncoursepage>1</visibleoncoursepage>
  <visibleold>1</visibleold>
  <groupmode>0</groupmode>
  <groupingid>0</groupingid>
  <completion>2</completion>
  <completiongradeitemnumber>$@NULL@$</completiongradeitemnumber>
  <completionpassgrade>1</completionpassgrade>
  <completionview>1</completionview>
  <completionexpected>0</completionexpected>
  <availability>$@NULL@$</availability>
  <showdescription>0</showdescription>
  <downloadcontent>1</downloadcontent>
  <lang></lang>
  <tags>
  </tags>
</module>
'''

    def _xml_quiz(self, module_id, qz, qids, cat_id) -> str:
        st = self.settings
        timelimit = st.time_limit * 60
        attempts = st.attempts
        grademethod = GRADEMETHOD_CODES.get(st.grading_method, 1)
        shuffle = "1" if st.shuffle_answers else "0"
        r = self.review

        # Якщо задано random_questions>0 — тест бере N ВИПАДКОВИХ питань зі
        # своєї категорії через question_set_reference (filtercondition).
        # Інакше — кожне питання ФІКСОВАНЕ через question_reference ->
        # questionbankentryid (ID question_bank_entry у questions.xml).
        # ВАЖЛИВО: question_set_reference для звичайного тесту = порожній
        # тест після Restore; question_reference для random = теж невірно.
        n_random = getattr(st, "random_questions", 0) or 0
        if n_random > 0:
            # обмежуємо кількість реальною кількістю питань у категорії
            n_slots = max(1, min(n_random, len(qz.questions)))
            grade = float(n_slots)
        else:
            n_slots = len(qids)
            grade = float(len(qz.questions)) or 1.0
        sumgrades = f"{grade:.5f}"

        slots = []
        for k in range(1, n_slots + 1):
            page = (k - 1) // max(1, self.questions_per_page) + 1
            if n_random > 0:
                # випадкове питання з категорії cat_id
                ref = (f'''        <question_set_reference id="{module_id * 1000 + k}">
          <usingcontextid>{100 + module_id}</usingcontextid>
          <component>mod_quiz</component>
          <questionarea>slot</questionarea>
          <questionscontextid>10</questionscontextid>
          <filtercondition>{{"qpage":0,"cat":"{cat_id},10","qperpage":100,"cpage":1,"tabname":"editq","sortdata":[],"jointype":2,"filter":{{"category":{{"jointype":1,"values":["{cat_id}"],"filteroptions":{{"includesubcategories":""}}}}}}}}</filtercondition>
        </question_set_reference>''')
            else:
                # фіксоване питання (пряме посилання на запис банку)
                qid = qids[k - 1]
                ref = (f'''        <question_reference id="{module_id * 1000 + k}">
          <usingcontextid>{100 + module_id}</usingcontextid>
          <component>mod_quiz</component>
          <questionarea>slot</questionarea>
          <questionbankentryid>{qid}</questionbankentryid>
          <version>$@NULL@$</version>
        </question_reference>''')
            slots.append(f'''      <question_instance id="{module_id * 1000 + k}">
        <quizid>{module_id}</quizid>
        <slot>{k}</slot>
        <page>{page}</page>
        <displaynumber>$@NULL@$</displaynumber>
        <requireprevious>0</requireprevious>
        <maxmark>1.0000000</maxmark>
        <quizgradeitemid>$@NULL@$</quizgradeitemid>
{ref}
      </question_instance>''')

        pass_frac = st.pass_percent / 100.0
        # feedbacks: як у реальному бекапі — порогові записи
        fb = [
            (11, "Відмінно!", 0.9 * grade, grade + 1.0),
            (12, "Зараховано.", pass_frac * grade, 0.9 * grade),
            (13, "Не складено.", 0.0, pass_frac * grade),
        ]
        feedbacks = []
        for fid, text, mn, mx in fb:
            feedbacks.append(f'''      <feedback id="{module_id * 100 + fid}">
        <feedbacktext>&lt;p&gt;{self._esc(text)}&lt;/p&gt;</feedbacktext>
        <feedbacktextformat>1</feedbacktextformat>
        <mingrade>{mn:.5f}</mingrade>
        <maxgrade>{mx:.5f}</maxgrade>
      </feedback>''')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<activity id="{module_id}" moduleid="{module_id}" modulename="quiz" contextid="{100 + module_id}">
  <quiz id="{module_id}">
    <name>{self._esc(qz.name)}</name>
    <intro>&lt;p&gt;{self._esc(qz.intro or st.info_text())}&lt;/p&gt;</intro>
    <introformat>1</introformat>
    <timeopen>0</timeopen>
    <timeclose>0</timeclose>
    <timelimit>{timelimit}</timelimit>
    <overduehandling>autosubmit</overduehandling>
    <graceperiod>0</graceperiod>
    <preferredbehaviour>{self.behaviour}</preferredbehaviour>
    <canredoquestions>0</canredoquestions>
    <attempts_number>{attempts}</attempts_number>
    <attemptonlast>0</attemptonlast>
    <grademethod>{grademethod}</grademethod>
    <decimalpoints>2</decimalpoints>
    <questiondecimalpoints>-1</questiondecimalpoints>
    <reviewattempt>{r["reviewattempt"]}</reviewattempt>
    <reviewcorrectness>{r["reviewcorrectness"]}</reviewcorrectness>
    <reviewmaxmarks>{r["reviewmaxmarks"]}</reviewmaxmarks>
    <reviewmarks>{r["reviewmarks"]}</reviewmarks>
    <reviewspecificfeedback>{r["reviewspecificfeedback"]}</reviewspecificfeedback>
    <reviewgeneralfeedback>{r["reviewgeneralfeedback"]}</reviewgeneralfeedback>
    <reviewrightanswer>{r["reviewrightanswer"]}</reviewrightanswer>
    <reviewoverallfeedback>{r["reviewoverallfeedback"]}</reviewoverallfeedback>
    <questionsperpage>{self.questions_per_page}</questionsperpage>
    <navmethod>{self.navmethod}</navmethod>
    <shuffleanswers>{shuffle}</shuffleanswers>
    <sumgrades>{sumgrades}</sumgrades>
    <grade>{grade:.5f}</grade>
    <timecreated>{self.now}</timecreated>
    <timemodified>{self.now}</timemodified>
    <password></password>
    <subnet></subnet>
    <browsersecurity>-</browsersecurity>
    <delay1>0</delay1>
    <delay2>0</delay2>
    <showuserpicture>1</showuserpicture>
    <showblocks>1</showblocks>
    <completionattemptsexhausted>0</completionattemptsexhausted>
    <completionminattempts>0</completionminattempts>
    <allowofflineattempts>0</allowofflineattempts>
    <subplugin_quizaccess_seb_quiz>
    </subplugin_quizaccess_seb_quiz>
    <quiz_grade_items>
    </quiz_grade_items>
    <question_instances>
{chr(10).join(slots)}
    </question_instances>
    <feedbacks>
{chr(10).join(feedbacks)}
    </feedbacks>
    <overrides>
    </overrides>
    <grades>
    </grades>
    <attempts>
    </attempts>
  </quiz>
</activity>
'''

    def _xml_quiz_inforef(self, cat_id, qids) -> str:
        cats = (f"  <question_categoryref>\n"
                f"    <question_category>\n      <id>{cat_id}</id>\n"
                f"    </question_category>\n"
                f"  </question_categoryref>")
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<inforef>\n'
                + cats + "\n</inforef>\n")

    def _xml_grades(self, module_id, qz, grade_item_id) -> str:
        pass_frac = self.settings.pass_percent / 100.0
        gmax = float(len(qz.questions) or 1)
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<activity_gradebook>
  <grade_items>
    <grade_item id="{grade_item_id}">
      <categoryid>2</categoryid>
      <itemname>{self._esc(qz.name)}</itemname>
      <itemtype>mod</itemtype>
      <itemmodule>quiz</itemmodule>
      <iteminstance>{module_id}</iteminstance>
      <itemnumber>0</itemnumber>
      <iteminfo>$@NULL@$</iteminfo>
      <idnumber></idnumber>
      <calculation>$@NULL@$</calculation>
      <gradetype>1</gradetype>
      <grademax>{gmax:.5f}</grademax>
      <grademin>0.00000</grademin>
      <scaleid>$@NULL@$</scaleid>
      <outcomeid>$@NULL@$</outcomeid>
      <gradepass>{pass_frac * gmax:.5f}</gradepass>
      <multfactor>1.00000</multfactor>
      <plusfactor>0.00000</plusfactor>
      <aggregationcoef>0.00000</aggregationcoef>
      <aggregationcoef2>0.00000</aggregationcoef2>
      <weightoverride>0</weightoverride>
      <sortorder>{grade_item_id}</sortorder>
      <display>0</display>
      <decimals>$@NULL@$</decimals>
      <hidden>0</hidden>
      <locked>0</locked>
      <locktime>0</locktime>
      <needsupdate>0</needsupdate>
      <timecreated>{self.now}</timecreated>
      <timemodified>{self.now}</timemodified>
    </grade_item>
  </grade_items>
  <grade_letters>
  </grade_letters>
</activity_gradebook>
'''

    # ---------------------------------------------------------- XML: gradebook
    def _xml_gradebook(self, module_map) -> str:
        ts = self.now
        # загальна макс. оцінка = сума питань усіх тестів
        total_max = float(sum(len(qz.questions) or 1
                              for _, _, qz in module_map)) or 100.0
        items = [f'''    <grade_item id="1">
      <categoryid>$@NULL@$</categoryid>
      <itemname>$@NULL@$</itemname>
      <itemtype>course</itemtype>
      <itemmodule>$@NULL@$</itemmodule>
      <iteminstance>2</iteminstance>
      <itemnumber>$@NULL@$</itemnumber>
      <iteminfo>$@NULL@$</iteminfo>
      <idnumber>$@NULL@$</idnumber>
      <calculation>$@NULL@$</calculation>
      <gradetype>1</gradetype>
      <grademax>{total_max:.5f}</grademax>
      <grademin>0.00000</grademin>
      <scaleid>$@NULL@$</scaleid>
      <outcomeid>$@NULL@$</outcomeid>
      <gradepass>0.00000</gradepass>
      <multfactor>1.00000</multfactor>
      <plusfactor>0.00000</plusfactor>
      <aggregationcoef>0.00000</aggregationcoef>
      <aggregationcoef2>0.00000</aggregationcoef2>
      <weightoverride>0</weightoverride>
      <sortorder>1</sortorder>
      <display>0</display>
      <decimals>$@NULL@$</decimals>
      <hidden>0</hidden>
      <locked>0</locked>
      <locktime>0</locktime>
      <needsupdate>0</needsupdate>
      <timecreated>{ts}</timecreated>
      <timemodified>{ts}</timemodified>
    </grade_item>''']

        pass_frac = self.settings.pass_percent / 100.0
        for n, (module_id, si, qz) in enumerate(module_map, 2):
            gmax = float(len(qz.questions) or 1)
            items.append(f'''    <grade_item id="{n}">
      <categoryid>2</categoryid>
      <itemname>{self._esc(qz.name)}</itemname>
      <itemtype>mod</itemtype>
      <itemmodule>quiz</itemmodule>
      <iteminstance>{module_id}</iteminstance>
      <itemnumber>0</itemnumber>
      <iteminfo>$@NULL@$</iteminfo>
      <idnumber></idnumber>
      <calculation>$@NULL@$</calculation>
      <gradetype>1</gradetype>
      <grademax>{gmax:.5f}</grademax>
      <grademin>0.00000</grademin>
      <scaleid>$@NULL@$</scaleid>
      <outcomeid>$@NULL@$</outcomeid>
      <gradepass>{pass_frac * gmax:.5f}</gradepass>
      <multfactor>1.00000</multfactor>
      <plusfactor>0.00000</plusfactor>
      <aggregationcoef>0.00000</aggregationcoef>
      <aggregationcoef2>0.00000</aggregationcoef2>
      <weightoverride>0</weightoverride>
      <sortorder>{n}</sortorder>
      <display>0</display>
      <decimals>$@NULL@$</decimals>
      <hidden>0</hidden>
      <locked>0</locked>
      <locktime>0</locktime>
      <needsupdate>0</needsupdate>
      <timecreated>{ts}</timecreated>
      <timemodified>{ts}</timemodified>
    </grade_item>''')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<gradebook>
  <attributes>
  </attributes>
  <grade_categories>
    <grade_category id="2">
      <parent>$@NULL@$</parent>
      <depth>1</depth>
      <path>/2/</path>
      <fullname>?</fullname>
      <aggregation>13</aggregation>
      <keephigh>0</keephigh>
      <droplow>0</droplow>
      <aggregateonlygraded>1</aggregateonlygraded>
      <aggregateoutcomes>0</aggregateoutcomes>
      <timecreated>{ts}</timecreated>
      <timemodified>{ts}</timemodified>
      <hidden>0</hidden>
    </grade_category>
  </grade_categories>
  <grade_items>
{chr(10).join(items)}
  </grade_items>
  <grade_letters>
  </grade_letters>
  <grade_settings>
  </grade_settings>
</gradebook>
'''


# ---------------------------------------------------------------------------
# Високорівневий API: сирі файли → MbzCourse
# ---------------------------------------------------------------------------

_RAW_EXTS = (".txt", ".docx", ".doc", ".csv", ".xlsx", ".xlsm",
             ".html", ".htm")


def _natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", name)]


def _read_any(path: str) -> str:
    """Читає файл будь-якого підтримуваного формату у текст."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".aiken"):
        with open(path, "rb") as f:
            raw = f.read()
        try:
            from converter_core import decode_bytes
            return decode_bytes(raw)
        except ImportError:
            return raw.decode("utf-8-sig", errors="replace")
    # решта — через converter_core.parse_file → відновлення Aiken
    from converter_core import parse_file, to_aiken
    qs = parse_file(path)
    return to_aiken(qs)


def files_to_course(file_paths: List[str],
                    settings: GlobalSettings,
                    topic_overrides: Optional[List[str]] = None,
                    course_fullname: str = "",
                    course_shortname: str = "") -> Tuple[MbzCourse, str]:
    """
    Масове перетворення сирих файлів у структуру курсу.
    1 файл = 1 секція = 1 тест. Сортування natural (Тема 2 < Тема 10).
    Повертає (MbzCourse, звіт).
    """
    parser = MoodleCourseGenerator(settings)
    paths = sorted(file_paths,
                   key=lambda p: _natural_key(os.path.basename(p)))
    course = MbzCourse(
        fullname=course_fullname or settings.course_name,
        shortname=course_shortname or re.sub(r"\s+", "_",
                                             settings.course_name)[:32],
        summary=settings.info_text())
    reports = []

    for i, path in enumerate(paths, 1):
        fname = os.path.basename(path)
        try:
            text = _read_any(path)
            questions = parser.parse_aiken(text)
        except Exception as e:
            reports.append(f"  ⚠ {fname}: пропущено (помилка читання: {e})")
            continue
        if not questions:
            reports.append(f"  ⚠ {fname}: пропущено (немає валідних питань)")
            continue

        if topic_overrides and (i - 1) < len(topic_overrides) \
                and topic_overrides[i - 1]:
            clean = topic_overrides[i - 1]
        else:
            clean = MoodleCourseGenerator._clean_filename(fname)

        sec_title = f"{settings.period_prefix} {i}: {clean}"
        quiz = CourseQuiz(
            name=f"Тест: {settings.period_prefix} {i} — {clean}",
            intro=settings.info_text(),
            questions=questions,
            category_name=f"{settings.course_name} / {sec_title}")
        course.sections.append(CourseSection(title=sec_title,
                                             quizzes=[quiz]))
        reports.append(f"  ✔ {fname}: {len(questions)} питань")

    head = [f"Секцій створено: {len(course.sections)}",
            f"Всього питань: "
            f"{sum(len(s.quizzes[0].questions) for s in course.sections)}",
            ""]
    return course, "\n".join(head + reports)


def build_mbz_from_files(file_paths: List[str],
                         settings: GlobalSettings,
                         out_path: str,
                         topic_overrides: Optional[List[str]] = None,
                         course_fullname: str = "",
                         course_shortname: str = "",
                         review_preset: str = "standard",
                         behaviour: str = "deferredfeedback") -> str:
    """Повний конвеєр: сирі файли → .mbz (tar.gz) на диску. Повертає звіт."""
    course, report = files_to_course(file_paths, settings, topic_overrides,
                                     course_fullname, course_shortname)
    if not course.sections:
        raise ValueError("Жодного валідного файлу для пакування в .mbz")
    builder = MbzBuilder(settings, review_preset=review_preset,
                         behaviour=behaviour)
    data = builder.build(course)
    with open(out_path, "wb") as f:
        f.write(data)
    return report + f"\n\nФайл збережено: {out_path} " \
                    f"({len(data) / 1024:.1f} КБ)"
