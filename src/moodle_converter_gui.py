# -*- coding: utf-8 -*-
"""
Moodle Test Converter — GUI (Ukrainian)
Converts test files (.txt .docx .xlsx .csv .html) with marked correct answers
into Moodle import formats: GIFT, Moodle XML, Aiken.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Lazy import: converter_core (and its heavy deps docx/openpyxl) is loaded
# only when a conversion/preview is actually requested, so the GUI window
# appears instantly.
parse_file = to_gift = to_moodle_xml = to_aiken = None


def _load_core():
    global parse_file, to_gift, to_moodle_xml, to_aiken
    if parse_file is None:
        from converter_core import (parse_file as _pf, to_gift as _tg,
                                    to_moodle_xml as _tx, to_aiken as _ta)
        parse_file, to_gift, to_moodle_xml, to_aiken = _pf, _tg, _tx, _ta

FORMATS = {
    "GIFT (.txt) — усі типи питань": ("gift", ".txt"),
    "Moodle XML (.xml) — усі типи питань": ("xml", ".xml"),
    "Aiken (.txt) — лише вибір однієї відповіді": ("aiken", ".txt"),
}

HELP_TEXT = """\
Як позначати правильні відповіді (усі підтримувані формати)
═══════════════════════════════════════════════════════════

У TXT / HTML:
  • зірочка в кінці:             б) Київ *
  • мітка на початку:            * б) Київ   ✓ б) Київ   + б) Київ
  • пари «+/-» (ключі ВНЗ):      + а) Азот   /   - б) Кисень
  • приписка:                    б) Київ (правильно)
  • markdown:                    б) **Київ**
  • рядок-ключ після питання:    Відповідь: Б  /  ANSWER: B  /  Відповідь: 2
                                 Ansver:3  /  Правильна відповідь:3
  • ключ у кінці файлу:          Відповіді: 1-Б, 2-В   або   Ключ: 1-а; 2-б
  • формат «QuestName:» (бази питань):
        QuestName:Текст питання
        варіант 1
        варіант 2
        варіант 3
        trueNum:3          ← номер правильної відповіді

У DOCX (Word):
  • ЖИРНИЙ шрифт відповіді
  • підкреслений текст відповіді
  • текст, ВИДІЛЕНИЙ КОЛЬОРОМ (маркер)
  • червоний колір шрифту відповіді
  • табличні шаблони (№ | Питання | Відповідь 1..N | Правильна)
  • ті самі текстові позначки, що й у TXT

У XLSX / CSV (таблиця):
  Питання | Варіант 1 | Варіант 2 | ... | Правильна
  У колонці «Правильна» — літера (А/Б/A/B), номер (1,2,3)
  або повний текст правильної відповіді.

Нумерація питань: 1.  1)  Запитання 1.  Питання №2.  Завдання 3.
Варіанти відповідей: літери (а б в / A B C) або цифри (1) 2) 3)).

Питання на відповідність (matching):
  а) Україна -> Київ
  б) Польща -> Варшава

Питання з короткою відповіддю:
  5. Назвіть найдовшу річку України
  Відповідь: Дніпро

Питання так/ні (вірно/невірно) визначаються автоматично.

Формат QuestName (медичні/екзаменаційні бази):
  QuestName:Текст питання
  перший варіант
  другий варіант
  третій варіант
  trueNum:3
  (також: Ansver:3, Правильна відповідь:3)

Імпорт у Moodle:
  Курс → Банк питань → Імпорт → оберіть формат файлу → Завантажити.
  Для GIFT-файлу з категорією поставте галочку «З категорій із файлу».
"""


ABOUT_TEXT = """\
Moodle Test Converter
Конвертер тестових завдань у формати Moodle (GIFT / Moodle XML / Aiken)

ЛІЦЕНЗІЙНА УГОДА ТА ВІДМОВА ВІД ВІДПОВІДАЛЬНОСТІ
═══════════════════════════════════════════════

1. ЗАГАЛЬНІ ПОЛОЖЕННЯ
   Ця програма поширюється безкоштовно («як є», англ. "AS IS") для
   навчальних та адміністративних потреб. Використовуючи програму,
   ви повністю приймаєте умови цієї угоди. Якщо ви не згодні з
   будь-яким пунктом — припиніть використання програми.

2. ВІДМОВА ВІД ВІДПОВІДАЛЬНОСТІ
   Розробник НЕ несе жодної відповідальності за:
   • будь-які прямі, непрямі, випадкові або наслідкові збитки,
     втрату даних, втрату прибутку чи інші втрати, що виникли
     внаслідок використання або неможливості використання програми;
   • коректність, повноту чи точність результатів конвертації.
     Результат конвертації ОБОВ'ЯЗКОВО має бути перевірений
     користувачем перед імпортом у Moodle та перед використанням
     у навчальному процесі або оцінюванні;
   • наслідки помилок у вихідних файлах користувача (неправильно
     позначені відповіді, помилки у формулюваннях питань тощо);
   • роботу сторонніх платформ (Moodle), сумісність з майбутніми
     версіями Moodle, а також зміни у форматах GIFT/XML/Aiken;
   • порушення авторських прав третіх осіб, допущені користувачем
     при обробці чужих матеріалів.

3. ВІДПОВІДАЛЬНІСТЬ КОРИСТУВАЧА
   Користувач самостійно відповідає за:
   • законність оброблюваних матеріалів (авторські права на тести,
     персональні дані тощо);
   • перевірку змісту питань і правильність позначення відповідей
     до та після конвертації;
   • дотримання правил своєї організації та платформи Moodle.

4. ГАРАНТІЇ
   Програма надається БЕЗ БУДЬ-ЯКИХ ГАРАНТІЙ, явних чи неявних,
   включно з гарантіями придатності для певної мети.

5. КОНФІДЕНЦІЙНІСТЬ
   Програма працює повністю офлайн і НЕ збирає, НЕ зберігає та
   НЕ передає жодних персональних даних чи вмісту файлів.

6. СТОРОННІ КОМПОНЕНТИ
   Програма містить компоненти з відкритим кодом (Python, python-docx,
   openpyxl), що поширюються за їхніми власними ліцензіями
   (PSF License, MIT License).

Використовуючи програму, ви підтверджуєте, що прочитали,
зрозуміли та погоджуєтесь із усіма пунктами цієї угоди.
"""


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Moodle Test Converter — повний набір інструментів")
        self.geometry("960x700")
        self.minsize(760, 560)
        self.files = []
        self._build()

    # ------------------------------------------------------------------ UI
    def _build(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)

        tab_conv = ttk.Frame(nb)
        tab_students = ttk.Frame(nb)
        tab_gemini = ttk.Frame(nb)
        tab_branch = ttk.Frame(nb)
        tab_api = ttk.Frame(nb)
        tab_course = ttk.Frame(nb)
        nb.add(tab_conv, text=" 🔄 Конвертер ")
        nb.add(tab_students, text=" 👥 Списки студентів ")
        nb.add(tab_gemini, text=" ✨ Генерація тестів (LLM) ")
        nb.add(tab_branch, text=" 🌿 Розгалужені сценарії ")
        nb.add(tab_api, text=" 🔗 Moodle API ")
        nb.add(tab_course, text=" 📦 Генератор курсу ")

        self._build_converter_tab(tab_conv)
        self._build_students_tab(tab_students)
        self._build_gemini_tab(tab_gemini)
        self._build_branch_tab(tab_branch)
        self._build_api_tab(tab_api)
        self._build_course_tab(tab_course)

    # ------------------------------------------------------ CONVERTER TAB
    def _build_converter_tab(self, root):
        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")

        ttk.Button(top, text="➕ Додати файли…", command=self.add_files
                   ).pack(side="left")
        ttk.Button(top, text="📂 Додати папку…", command=self.add_folder
                   ).pack(side="left", padx=6)
        ttk.Button(top, text="🗑 Очистити", command=self.clear_files
                   ).pack(side="left")

        ttk.Label(top, text="Формат:").pack(side="left", padx=(16, 4))
        self.fmt_var = tk.StringVar(value=list(FORMATS)[0])
        ttk.Combobox(top, textvariable=self.fmt_var, values=list(FORMATS),
                     state="readonly", width=44).pack(side="left")

        ttk.Label(top, text="Категорія:").pack(side="left", padx=(16, 4))
        self.cat_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.cat_var, width=18).pack(side="left")

        # режим кількості правильних відповідей
        mode = ttk.Frame(root, padding=(8, 0, 8, 2))
        mode.pack(fill="x")
        ttk.Label(mode, text="Правильних відповідей:").pack(side="left")
        self.single_var = tk.StringVar(value="multi")
        ttk.Radiobutton(mode, text="Декілька (автовизначення з розмітки)",
                        variable=self.single_var, value="multi"
                        ).pack(side="left", padx=8)
        ttk.Radiobutton(mode, text="Одна (лише перша позначена)",
                        variable=self.single_var, value="single"
                        ).pack(side="left")

        mid = ttk.Frame(root, padding=(8, 0, 8, 4))
        mid.pack(fill="both", expand=True)

        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Файли для конвертації (.txt .doc .docx .xlsx .csv .html):")\
            .pack(anchor="w")
        self.listbox = tk.Listbox(left, height=10)
        self.listbox.pack(fill="both", expand=True, pady=4)

        ttk.Label(mid, text="Попередній перегляд / журнал:").pack(anchor="w")
        pw = ttk.Frame(root, padding=(8, 0, 8, 4))
        pw.pack(fill="both", expand=True)
        self.preview = tk.Text(pw, height=14, wrap="none", font=("Consolas", 9))
        sy = ttk.Scrollbar(pw, orient="vertical", command=self.preview.yview)
        self.preview.configure(yscrollcommand=sy.set)
        sy.pack(side="right", fill="y")
        self.preview.pack(fill="both", expand=True)

        # progress bar for batch conversion of many files
        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.pack(fill="x", padx=8, pady=(0, 2))
        self.status_var = tk.StringVar(value="Готово до роботи")
        ttk.Label(root, textvariable=self.status_var, anchor="w",
                  padding=(8, 0)).pack(fill="x")

        bot = ttk.Frame(root, padding=8)
        bot.pack(fill="x")
        ttk.Button(bot, text="👁 Переглянути", command=self.preview_file
                   ).pack(side="left")
        ttk.Button(bot, text="❓ Довідка", command=self.show_help
                   ).pack(side="left", padx=6)
        ttk.Button(bot, text="ℹ️ Інформація", command=self.show_about
                   ).pack(side="left")
        self.convert_btn = ttk.Button(bot, text="⚙ КОНВЕРТУВАТИ ВСЕ",
                                      command=self.convert_all)
        self.convert_btn.pack(side="right")

    # ------------------------------------------------------ STUDENTS TAB
    def _build_students_tab(self, root):
        top = ttk.Frame(root, padding=8)
        top.pack(fill="both", expand=True)

        ttk.Label(top, text="Вставте список студентів (по одному в рядок):\n"
                  "Формати: «Прізвище Ім'я», «Прізвище Ім'я По-батькові», "
                  "«Прізвище, Ім'я, email»",
                  justify="left").pack(anchor="w")
        self.students_text = tk.Text(top, height=10, wrap="word",
                                     font=("Consolas", 10))
        self.students_text.pack(fill="both", expand=True, pady=4)

        opts = ttk.Frame(top)
        opts.pack(fill="x", pady=4)
        ttk.Label(opts, text="Курс (course1):").grid(row=0, column=0,
                                                     sticky="w")
        self.stu_course = ttk.Entry(opts, width=18)
        self.stu_course.grid(row=0, column=1, padx=4)
        ttk.Label(opts, text="Група (group1):").grid(row=0, column=2,
                                                     sticky="w")
        self.stu_group = ttk.Entry(opts, width=18)
        self.stu_group.grid(row=0, column=3, padx=4)
        ttk.Label(opts, text="Когорта (cohort1):").grid(row=1, column=0,
                                                        sticky="w")
        self.stu_cohort = ttk.Entry(opts, width=18)
        self.stu_cohort.grid(row=1, column=1, padx=4)
        ttk.Label(opts, text="Пароль:").grid(row=1, column=2, sticky="w")
        self.stu_pass = ttk.Entry(opts, width=18)
        self.stu_pass.insert(0, "ChangeMe123!")
        self.stu_pass.grid(row=1, column=3, padx=4)

        btns = ttk.Frame(top)
        btns.pack(fill="x")
        ttk.Button(btns, text="👁 Перегляд списку",
                   command=self.students_preview).pack(side="left")
        ttk.Button(btns, text="💾 Експорт CSV (користувачі)",
                   command=lambda: self.students_export("users")
                   ).pack(side="left", padx=4)
        ttk.Button(btns, text="💾 Експорт CSV (когорта)",
                   command=lambda: self.students_export("cohort")
                   ).pack(side="left", padx=4)
        ttk.Button(btns, text="💾 Експорт XLSX",
                   command=lambda: self.students_export("xlsx")
                   ).pack(side="left", padx=4)

        self.students_log = tk.Text(top, height=8, wrap="none",
                                    font=("Consolas", 9))
        self.students_log.pack(fill="both", expand=True, pady=4)

    def students_preview(self):
        from students_module import parse_students
        sts = parse_students(self.students_text.get("1.0", "end"))
        self.students_log.delete("1.0", "end")
        ok = [s for s in sts if not s.get("error") or s["firstname"]]
        self.students_log.insert("end",
            f"Розпізнано студентів: {len(ok)} з {len(sts)}\n\n")
        for i, s in enumerate(sts, 1):
            flag = "⚠ " if s.get("error") else "✔ "
            self.students_log.insert("end",
                f"{flag}{i}. {s['lastname']} {s['firstname']} "
                f"→ {s['username']} {s['email']}\n")
            if s.get("error"):
                self.students_log.insert("end", f"     {s['error']}\n")

    def students_export(self, kind):
        from students_module import (parse_students, students_to_moodle_csv,
                                     students_to_cohort_csv,
                                     students_to_xlsx_rows)
        sts = parse_students(self.students_text.get("1.0", "end"))
        ok = [s for s in sts if s["firstname"]]
        if not ok:
            messagebox.showinfo("Список порожній",
                                "Немає коректно розпізнаних студентів.")
            return
        if kind == "xlsx":
            path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")])
            if not path:
                return
            from openpyxl import Workbook
            wb = Workbook(); ws = wb.active
            for row in students_to_xlsx_rows(ok):
                ws.append(row)
            wb.save(path)
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if not path:
                return
            pwd = self.stu_pass.get()
            if kind == "users":
                content = students_to_moodle_csv(
                    ok, self.stu_course.get().strip(),
                    self.stu_group.get().strip(), pwd)
            else:
                content = students_to_cohort_csv(
                    ok, self.stu_cohort.get().strip(), pwd)
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(content)
        self.students_log.insert("end",
            f"\n💾 Збережено {len(ok)} студентів у {os.path.basename(path)}\n")

    # ------------------------------------------------------ GEMINI TAB
    def _build_gemini_tab(self, root):
        from llm_module import PROVIDERS
        top = ttk.Frame(root, padding=8)
        top.pack(fill="both", expand=True)

        # --- provider row ---
        provf = ttk.Frame(top)
        provf.pack(fill="x", pady=(0, 4))
        ttk.Label(provf, text="Провайдер LLM:",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.llm_provider = ttk.Combobox(provf, values=list(PROVIDERS),
                                         state="readonly", width=30)
        self.llm_provider.set("Google Gemini")
        self.llm_provider.pack(side="left", padx=6)
        self.llm_provider.bind("<<ComboboxSelected>>",
                               lambda e: self._on_provider_change())
        self.llm_free_lbl = ttk.Label(provf, text="", foreground="#0a7a0a",
                                      font=("Segoe UI", 9, "bold"))
        self.llm_free_lbl.pack(side="left", padx=6)
        ttk.Button(provf, text="❓ Як отримати ключ",
                   command=self._show_provider_howto).pack(side="left",
                                                           padx=6)

        # --- API key + custom base URL row ---
        keyf = ttk.Frame(top)
        keyf.pack(fill="x", pady=(0, 4))
        ttk.Label(keyf, text="🔑 API-ключ:",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.gem_key = ttk.Entry(keyf, width=42, show="•")
        self.gem_key.pack(side="left", padx=6)
        ttk.Button(keyf, text="Показати", command=lambda: self.gem_key.configure(
            show="" if self.gem_key.cget("show") == "•" else "•")).pack(
            side="left")
        self.llm_base_lbl = ttk.Label(keyf, text="  Base URL:")
        self.llm_base = ttk.Entry(keyf, width=30)
        # hidden by default; shown only for custom OpenAI-compatible
        self.llm_base_lbl.pack_forget()

        # --- model fetch row ---
        modf = ttk.Frame(top)
        modf.pack(fill="x", pady=(0, 6))
        self.llm_fetch_btn = ttk.Button(
            modf, text="🔄 Отримати моделі з сервера",
            command=self._fetch_models)
        self.llm_fetch_btn.pack(side="left")
        ttk.Label(modf, text="Модель:").pack(side="left", padx=(12, 2))
        self.gem_model = ttk.Combobox(modf, values=[], state="readonly",
                                      width=40)
        self.gem_model.pack(side="left")
        self.llm_models_status = ttk.Label(modf, text="(спочатку введіть "
                                           "ключ і натисніть «Отримати "
                                           "моделі»)", foreground="#666")
        self.llm_models_status.pack(side="left", padx=8)

        # settings grid
        grid = ttk.LabelFrame(top, text=" Настройки генерації ", padding=6)
        grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="Тема:").grid(row=0, column=0, sticky="w")
        self.gem_topic = ttk.Entry(grid, width=42)
        self.gem_topic.grid(row=0, column=1, columnspan=3, sticky="we",
                            padx=4)
        ttk.Label(grid, text="Кількість питань:").grid(row=1, column=0,
                                                        sticky="w")
        self.gem_n = ttk.Spinbox(grid, from_=1, to=100, width=6)
        self.gem_n.set(10)
        self.gem_n.grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(grid, text="Тип питань:").grid(row=1, column=2, sticky="w")
        self.gem_type = ttk.Combobox(grid, values=[
            "Вибір однієї відповіді", "Вибір кількох відповідей",
            "Так/Ні", "Коротка відповідь", "Відповідність (matching)",
            "Змішаний набір"], state="readonly", width=26)
        self.gem_type.set("Вибір однієї відповіді")
        self.gem_type.grid(row=1, column=3, sticky="w", padx=4)
        ttk.Label(grid, text="Складність:").grid(row=2, column=0, sticky="w")
        self.gem_level = ttk.Combobox(grid, values=["Легка", "Середня",
                                                    "Складна"],
                                      state="readonly", width=10)
        self.gem_level.set("Середня")
        self.gem_level.grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(grid, text="Аудиторія:").grid(row=2, column=2, sticky="w")
        self.gem_aud = ttk.Entry(grid, width=26)
        self.gem_aud.insert(0, "студенти")
        self.gem_aud.grid(row=2, column=3, sticky="w", padx=4)
        ttk.Label(grid, text="Варіантів відповіді:").grid(row=3, column=0,
                                                          sticky="w")
        self.gem_opts = ttk.Spinbox(grid, from_=2, to=6, width=6)
        self.gem_opts.set(4)
        self.gem_opts.grid(row=3, column=1, sticky="w", padx=4)
        self.gem_fb = tk.BooleanVar(value=True)
        ttk.Checkbutton(grid, text="Фідбек до варіантів",
                        variable=self.gem_fb).grid(row=3, column=2,
                                                   columnspan=2, sticky="w")
        ttk.Label(grid, text="Додаткові вимоги:").grid(row=4, column=0,
                                                        sticky="w")
        self.gem_extra = ttk.Entry(grid, width=42)
        self.gem_extra.grid(row=4, column=1, columnspan=3, sticky="we",
                            padx=4)
        grid.columnconfigure(3, weight=1)

        ttk.Button(top, text="✨ ЗГЕНЕРУВАТИ ТЕСТИ",
                   command=self.gemini_generate).pack(pady=6)
        self._on_provider_change()  # init free/paid badge

        self.gem_out = tk.Text(top, height=14, wrap="none",
                               font=("Consolas", 9))
        self.gem_out.pack(fill="both", expand=True)

        btns = ttk.Frame(top)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="💾 Зберегти як TXT (для конвертера)",
                   command=lambda: self._save_text(self.gem_out, ".txt")
                   ).pack(side="left")
        ttk.Button(btns, text="➡ У конвертер (GIFT)",
                   command=lambda: self._gem_to_converter("gift")
                   ).pack(side="left", padx=4)
        ttk.Button(btns, text="➡ У конвертер (Aiken)",
                   command=lambda: self._gem_to_converter("aiken")
                   ).pack(side="left", padx=4)

    def _on_provider_change(self):
        from llm_module import PROVIDERS
        info = PROVIDERS[self.llm_provider.get()]
        self.llm_free_lbl.configure(
            text="БЕЗКОШТОВНО" if info["free"] else "ПЛАТНО",
            foreground="#0a7a0a" if info["free"] else "#b00000")
        if info.get("custom_base"):
            self.llm_base_lbl.pack(side="left", padx=(12, 2))
            self.llm_base.pack(side="left")
        else:
            self.llm_base_lbl.pack_forget()
            self.llm_base.pack_forget()
        self.gem_model.configure(values=[])
        self.gem_model.set("")
        self.llm_models_status.configure(
            text="(введіть ключ і натисніть «Отримати моделі»)")

    def _show_provider_howto(self):
        from llm_module import PROVIDERS
        name = self.llm_provider.get()
        info = PROVIDERS[name]
        win = tk.Toplevel(self)
        win.title(f"Як отримати API-ключ — {name}")
        win.geometry("620x300")
        t = tk.Text(win, wrap="word", font=("Segoe UI", 10), padx=12,
                    pady=12)
        badge = "БЕЗКОШТОВНИЙ" if info["free"] else "ПЛАТНИЙ"
        t.insert("1.0", f"{name}  —  {badge}\n\n{info['howto']}")
        t.configure(state="disabled")
        t.pack(fill="both", expand=True)

    def _fetch_models(self):
        """Query the provider server for the list of available models."""
        import threading
        from llm_module import list_models
        provider = self.llm_provider.get()
        key = self.gem_key.get().strip()
        base = self.llm_base.get().strip()
        if not key:
            messagebox.showwarning("LLM", "Спочатку введіть API-ключ.")
            return
        self.llm_fetch_btn.configure(state="disabled")
        self.llm_models_status.configure(text="⏳ запит до сервера...")

        def work():
            try:
                models = list_models(provider, key, base)
            except Exception as e:
                models = None
                err = str(e)
            def done():
                self.llm_fetch_btn.configure(state="normal")
                if models:
                    self.gem_model.configure(values=models)
                    # preselect a sensible default
                    pref = next((m for m in models if "flash" in m),
                                models[0])
                    self.gem_model.set(pref)
                    self.llm_models_status.configure(
                        text=f"✅ доступно моделей: {len(models)}",
                        foreground="#0a7a0a")
                else:
                    self.llm_models_status.configure(
                        text=f"❌ {err if not models else 'немає моделей'}",
                        foreground="#b00000")
            self.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    def gemini_generate(self):
        import threading
        key = self.gem_key.get().strip()
        if not key:
            messagebox.showwarning("LLM", "Спочатку введіть API-ключ.")
            return
        model = self.gem_model.get().strip()
        if not model:
            messagebox.showwarning(
                "LLM",
                "Натисніть «Отримати моделі з сервера» і оберіть модель.")
            return
        provider = self.llm_provider.get()
        base = self.llm_base.get().strip()
        self.gem_out.delete("1.0", "end")
        self.gem_out.insert("end", f"⏳ Генерація ({provider} / {model})...\n")

        def work():
            try:
                from llm_module import generate_tests
                text = generate_tests(
                    provider, key, model, self.gem_topic.get(),
                    int(self.gem_n.get()), self.gem_type.get(),
                    self.gem_level.get(), self.gem_aud.get(),
                    int(self.gem_opts.get()),
                    with_feedback=self.gem_fb.get(),
                    extra=self.gem_extra.get(), base_url=base)
            except Exception as e:
                text = f"ПОМИЛКА: {e}"
            self.after(0, lambda: (self.gem_out.delete("1.0", "end"),
                                   self.gem_out.insert("1.0", text)))
        threading.Thread(target=work, daemon=True).start()

    def _save_text(self, widget, ext):
        path = filedialog.asksaveasfilename(defaultextension=ext)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(widget.get("1.0", "end"))

    def _gem_to_converter(self, fmt):
        from converter_core import (parse_numbered_lines, post_process,
                                    to_gift, to_aiken, to_moodle_xml)
        text = self.gem_out.get("1.0", "end")
        qs = post_process(parse_numbered_lines(text.splitlines()))
        if not qs:
            messagebox.showinfo("Конвертер", "Питань не розпізнано.")
            return
        content = {"gift": to_gift, "aiken": to_aiken,
                   "xml": to_moodle_xml}[fmt](qs)
        path = filedialog.asksaveasfilename(
            defaultextension={"gift": ".txt", "aiken": ".txt",
                              "xml": ".xml"}[fmt])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Готово",
                                f"Експортовано {len(qs)} питань у {fmt}.")

    # ------------------------------------------------------ BRANCHING TAB
    def _build_branch_tab(self, root):
        top = ttk.Frame(root, padding=8)
        top.pack(fill="both", expand=True)

        # --- provider row (multi-LLM, same as test generator) ---
        from llm_module import PROVIDERS
        provf = ttk.Frame(top)
        provf.pack(fill="x", pady=(0, 4))
        ttk.Label(provf, text="Провайдер LLM:",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.br_provider = ttk.Combobox(provf, values=list(PROVIDERS),
                                        state="readonly", width=28)
        self.br_provider.set("Google Gemini")
        self.br_provider.pack(side="left", padx=6)
        self.br_provider.bind("<<ComboboxSelected>>",
                              lambda e: self._on_br_provider_change())
        self.br_free_lbl = ttk.Label(provf, text="", foreground="#0a7a0a",
                                     font=("Segoe UI", 9, "bold"))
        self.br_free_lbl.pack(side="left", padx=4)
        ttk.Button(provf, text="❓ Як отримати ключ",
                   command=self._show_br_howto).pack(side="left", padx=4)

        # --- API key + custom base + fetch models ---
        keyf = ttk.Frame(top)
        keyf.pack(fill="x", pady=(0, 4))
        ttk.Label(keyf, text="🔑 API-ключ:",
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        self.br_key = ttk.Entry(keyf, width=36, show="•")
        self.br_key.pack(side="left", padx=6)
        self.br_base_lbl = ttk.Label(keyf, text="  Base URL:")
        self.br_base = ttk.Entry(keyf, width=24)
        self.br_base_lbl.pack_forget()

        modf = ttk.Frame(top)
        modf.pack(fill="x", pady=(0, 6))
        self.br_fetch_btn = ttk.Button(
            modf, text="🔄 Отримати моделі з сервера",
            command=self._br_fetch_models)
        self.br_fetch_btn.pack(side="left")
        ttk.Label(modf, text="Модель:").pack(side="left", padx=(12, 2))
        self.br_model = ttk.Combobox(modf, values=[], state="readonly",
                                     width=36)
        self.br_model.pack(side="left")
        self.br_models_status = ttk.Label(
            modf, text="(введіть ключ і натисніть «Отримати моделі»)",
            foreground="#666")
        self.br_models_status.pack(side="left", padx=8)
        self._on_br_provider_change()

        grid = ttk.LabelFrame(top, text=" Настройки сценарію (системний промпт вбудований) ",
                              padding=6)
        grid.pack(fill="x", pady=4)
        ttk.Label(grid, text="Тема (topic):").grid(row=0, column=0, sticky="w")
        self.br_topic = ttk.Entry(grid, width=46)
        self.br_topic.grid(row=0, column=1, columnspan=3, sticky="we", padx=4)
        ttk.Label(grid, text="Аудиторія:").grid(row=1, column=0, sticky="w")
        self.br_aud = ttk.Entry(grid, width=22)
        self.br_aud.insert(0, "студенти-медики 2 курсу")
        self.br_aud.grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(grid, text="Рівень складності:").grid(row=1, column=2,
                                                         sticky="w")
        self.br_level = ttk.Combobox(grid, values=["easy", "medium", "hard"],
                                     state="readonly", width=10)
        self.br_level.set("medium")
        self.br_level.grid(row=1, column=3, sticky="w", padx=4)
        ttk.Label(grid, text="Навчальні цілі (по 1 в рядок):").grid(
            row=2, column=0, sticky="nw")
        self.br_lo = tk.Text(grid, height=3, width=40, font=("Consolas", 9))
        self.br_lo.grid(row=2, column=1, columnspan=3, sticky="we", padx=4)
        ttk.Label(grid, text="Контекст:").grid(row=3, column=0, sticky="w")
        self.br_ctx = ttk.Entry(grid, width=46)
        self.br_ctx.grid(row=3, column=1, columnspan=3, sticky="we", padx=4)
        ttk.Label(grid, text="Стиль:").grid(row=4, column=0, sticky="w")
        self.br_style = ttk.Entry(grid, width=22)
        self.br_style.insert(0, "стисла клінічна мова")
        self.br_style.grid(row=4, column=1, sticky="w", padx=4)
        ttk.Label(grid, text="Модель балів:").grid(row=4, column=2, sticky="w")
        self.br_score = ttk.Entry(grid, width=22)
        self.br_score.insert(0, "[-2, -1, 0, +1, +2]")
        self.br_score.grid(row=4, column=3, sticky="w", padx=4)
        ttk.Label(grid, text="Обмеження:").grid(row=5, column=0, sticky="w")
        self.br_constr = ttk.Entry(grid, width=46)
        self.br_constr.grid(row=5, column=1, columnspan=3, sticky="we", padx=4)
        grid.columnconfigure(3, weight=1)

        btns = ttk.Frame(top)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="🌿 ЗГЕНЕРУВАТИ СЦЕНАРІЙ",
                   command=self.branch_generate).pack(side="left")
        ttk.Button(btns, text="🌳 Показати дерево",
                   command=self.branch_tree).pack(side="left", padx=4)
        ttk.Button(btns, text="💾 Зберегти сценарій (.txt)",
                   command=lambda: self._save_text(self.br_out, ".txt")
                   ).pack(side="left", padx=4)
        ttk.Button(btns, text="💾 Експорт GIFT для Moodle",
                   command=self.branch_gift).pack(side="left", padx=4)
        ttk.Button(btns, text="🎓 Експорт H5P (.json)",
                   command=self.branch_h5p).pack(side="left", padx=4)
        ttk.Button(btns, text="📄 Експорт JSON",
                   command=self.branch_json).pack(side="left", padx=4)

        self.br_out = tk.Text(top, height=16, wrap="none",
                              font=("Consolas", 9))
        self.br_out.pack(fill="both", expand=True)

    def _on_br_provider_change(self):
        from llm_module import PROVIDERS
        info = PROVIDERS[self.br_provider.get()]
        self.br_free_lbl.configure(
            text="БЕЗКОШТОВНО" if info["free"] else "ПЛАТНО",
            foreground="#0a7a0a" if info["free"] else "#b00000")
        if info.get("custom_base"):
            self.br_base_lbl.pack(side="left", padx=(10, 2))
            self.br_base.pack(side="left")
        else:
            self.br_base_lbl.pack_forget()
            self.br_base.pack_forget()
        self.br_model.configure(values=[])
        self.br_model.set("")
        self.br_models_status.configure(
            text="(введіть ключ і натисніть «Отримати моделі»)",
            foreground="#666")

    def _show_br_howto(self):
        from llm_module import PROVIDERS
        name = self.br_provider.get()
        info = PROVIDERS[name]
        win = tk.Toplevel(self)
        win.title(f"Як отримати API-ключ — {name}")
        win.geometry("620x300")
        t = tk.Text(win, wrap="word", font=("Segoe UI", 10), padx=12,
                    pady=12)
        badge = "БЕЗКОШТОВНИЙ" if info["free"] else "ПЛАТНИЙ"
        t.insert("1.0", f"{name}  —  {badge}\n\n{info['howto']}")
        t.configure(state="disabled")
        t.pack(fill="both", expand=True)

    def _br_fetch_models(self):
        import threading
        from llm_module import list_models
        provider = self.br_provider.get()
        key = self.br_key.get().strip()
        base = self.br_base.get().strip()
        if not key:
            messagebox.showwarning("Сценарії", "Спочатку введіть API-ключ.")
            return
        self.br_fetch_btn.configure(state="disabled")
        self.br_models_status.configure(text="⏳ запит до сервера...",
                                        foreground="#666")

        def work():
            err = ""
            try:
                models = list_models(provider, key, base)
            except Exception as e:
                models = None
                err = str(e)
            def done():
                self.br_fetch_btn.configure(state="normal")
                if models:
                    self.br_model.configure(values=models)
                    pref = next((m for m in models if "flash" in m
                                 or "pro" in m), models[0])
                    self.br_model.set(pref)
                    self.br_models_status.configure(
                        text=f"✅ доступно моделей: {len(models)}",
                        foreground="#0a7a0a")
                else:
                    self.br_models_status.configure(
                        text=f"❌ {err or 'немає моделей'}",
                        foreground="#b00000")
            self.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    def branch_generate(self):
        import threading
        key = self.br_key.get().strip()
        if not key:
            messagebox.showwarning("Сценарії", "Спочатку введіть API-ключ.")
            return
        model = self.br_model.get().strip()
        if not model:
            messagebox.showwarning(
                "Сценарії",
                "Натисніть «Отримати моделі з сервера» і оберіть модель.")
            return
        provider = self.br_provider.get()
        base = self.br_base.get().strip()
        self.br_out.delete("1.0", "end")
        self.br_out.insert("end",
                           f"⏳ Генерація сценарію ({provider} / {model})...\n")

        def work():
            try:
                from branching_module import generate_branching
                los = [l.strip() for l in
                       self.br_lo.get("1.0", "end").splitlines() if l.strip()]
                text = generate_branching(
                    provider, key, model, self.br_topic.get(),
                    self.br_aud.get(), self.br_level.get(), los,
                    self.br_ctx.get(), self.br_style.get(),
                    self.br_score.get(), self.br_constr.get(),
                    base_url=base)
            except Exception as e:
                text = f"ПОМИЛКА: {e}"
            self.after(0, lambda: (self.br_out.delete("1.0", "end"),
                                   self.br_out.insert("1.0", text)))
        threading.Thread(target=work, daemon=True).start()

    def branch_tree(self):
        """Читання згенерованого сценарію БЕЗ розмітки у вигляді дерева."""
        from branching_module import parse_scenario, tree_to_outline
        text = self.br_out.get("1.0", "end").strip()
        if not text or text.startswith("⏳") or text.startswith("ПОМИЛКА"):
            messagebox.showinfo("Дерево", "Спочатку згенеруйте сценарій.")
            return
        try:
            tree = parse_scenario(text)
            outline = tree_to_outline(tree)
        except Exception as e:
            messagebox.showerror("Дерево", f"Не вдалося розібрати: {e}")
            return
        win = tk.Toplevel(self)
        win.title("Ієрархічна структура сценарію")
        win.geometry("760x600")
        t = tk.Text(win, wrap="none", font=("Consolas", 10), padx=8, pady=8)
        t.insert("1.0", outline)
        t.configure(state="disabled")
        t.pack(fill="both", expand=True)

    def branch_gift(self):
        from branching_module import parse_scenario
        text = self.br_out.get("1.0", "end").strip()
        tree = parse_scenario(text)
        if not tree["gift"]:
            messagebox.showinfo("GIFT",
                                "У сценарії немає секції MOODLE_GIFT_EXPORT.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("GIFT", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(tree["gift"])
            messagebox.showinfo("GIFT", "Експортовано GIFT для Moodle.")

    def _branch_tree_or_warn(self):
        """Спільний крок експорту: зібрати дерево сценарію або попередити."""
        from branching_module import parse_scenario
        text = self.br_out.get("1.0", "end").strip()
        if not text or text.startswith("⏳") or text.startswith("ПОМИЛКА"):
            messagebox.showinfo("Експорт", "Спочатку згенеруйте сценарій.")
            return None
        try:
            tree = parse_scenario(text)
        except Exception as e:
            messagebox.showerror("Експорт", f"Не вдалося розібрати: {e}")
            return None
        if not tree.get("nodes"):
            messagebox.showinfo("Експорт",
                                "У сценарії немає вузлів (NODE_x).")
            return None
        return tree

    def branch_h5p(self):
        """Експорт сценарію у формат H5P Branching Scenario (content.json)."""
        from branching_module import export_h5p
        tree = self._branch_tree_or_warn()
        if tree is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="content.json",
            filetypes=[("H5P content.json", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(export_h5p(tree))
        except Exception as e:
            messagebox.showerror("H5P", f"Не вдалося зберегти: {e}")
            return
        messagebox.showinfo(
            "H5P",
            "Експортовано content.json для H5P Branching Scenario.\n\n"
            "Як використати: покладіть файл у папку content/ пакета .h5p "
            "(бібліотека H5P.BranchingScenario) або в Moodle: "
            "Інтерактивний вміст (H5P) → Завантажити.")

    def branch_json(self):
        """Експорт сценарію у універсальний JSON (чиста структура дерева)."""
        from branching_module import export_json
        tree = self._branch_tree_or_warn()
        if tree is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="scenario.json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(export_json(tree))
        except Exception as e:
            messagebox.showerror("JSON", f"Не вдалося зберегти: {e}")
            return
        messagebox.showinfo("JSON", "Експортовано scenario.json.")

    # ------------------------------------------------------ API TAB
    def _build_api_tab(self, root):
        top = ttk.Frame(root, padding=8)
        top.pack(fill="both", expand=True)

        frm = ttk.LabelFrame(top, text=" З'єднання з Moodle (Web Services) ",
                             padding=8)
        frm.pack(fill="x", pady=4)
        ttk.Label(frm, text="URL Moodle:").grid(row=0, column=0, sticky="w")
        self.api_url = ttk.Entry(frm, width=44)
        self.api_url.insert(0, "https://your-moodle.edu.ua")
        self.api_url.grid(row=0, column=1, sticky="we", padx=4)
        ttk.Label(frm, text="Токен (web service token):").grid(row=1,
                                                               column=0,
                                                               sticky="w")
        self.api_token = ttk.Entry(frm, width=44, show="•")
        self.api_token.grid(row=1, column=1, sticky="we", padx=4)
        frm.columnconfigure(1, weight=1)

        btns = ttk.Frame(top)
        btns.pack(fill="x", pady=4)
        ttk.Button(btns, text="🔌 Перевірити з'єднання",
                   command=self.api_test).pack(side="left")
        ttk.Button(btns, text="📚 Отримати курси",
                   command=self.api_courses).pack(side="left", padx=4)
        ttk.Button(btns, text="📤 Надіслати файл у Moodle (draft)",
                   command=self.api_upload).pack(side="left", padx=4)

        self.api_log = tk.Text(top, height=14, wrap="word",
                               font=("Consolas", 9))
        self.api_log.pack(fill="both", expand=True, pady=4)

        note = ttk.Label(top, foreground="#666",
                         text=("Примітка: прямий імпорт GIFT/XML у банк питань "
                               "потребує плагіна qformat на боці Moodle. Цей модуль "
                               "підтримує перевірку токена, список курсів і "
                               "завантаження файлів у draft-область."),
                         wraplength=820, justify="left")
        note.pack(anchor="w", pady=2)

    def _api_client(self):
        from moodle_api_module import MoodleAPI, MoodleAPIError
        return MoodleAPI(self.api_url.get(), self.api_token.get())

    def api_test(self):
        import threading, json
        self.api_log.delete("1.0", "end")
        self.api_log.insert("end", "⏳ Перевірка з'єднання...\n")

        def work():
            try:
                info = self._api_client().test_connection()
                txt = ("✅ З'єднання успішне!\n\n"
                       f"Сайт: {info.get('sitename')}\n"
                       f"Користувач: {info.get('fullname')} "
                       f"({info.get('username')})\n"
                       f"Версія Moodle: {info.get('release')}\n"
                       f"Функцій доступно: {len(info.get('functions', []))}\n")
            except Exception as e:
                txt = f"❌ ПОМИЛКА: {e}\n"
            self.after(0, lambda: (self.api_log.delete("1.0", "end"),
                                   self.api_log.insert("1.0", txt)))
        threading.Thread(target=work, daemon=True).start()

    def api_courses(self):
        import threading
        self.api_log.delete("1.0", "end")
        self.api_log.insert("end", "⏳ Завантаження курсів...\n")

        def work():
            try:
                courses = self._api_client().get_courses()
                lines = [f"Знайдено курсів: {len(courses)}\n"]
                for c in courses:
                    lines.append(f"  [{c.get('id')}] {c.get('fullname')}")
                txt = "\n".join(lines)
            except Exception as e:
                txt = f"❌ ПОМИЛКА: {e}"
            self.after(0, lambda: (self.api_log.delete("1.0", "end"),
                                   self.api_log.insert("1.0", txt)))
        threading.Thread(target=work, daemon=True).start()

    def api_upload(self):
        import threading
        path = filedialog.askopenfilename(title="Оберіть файл для надсилання")
        if not path:
            return
        self.api_log.insert("end", f"⏳ Надсилання {os.path.basename(path)}...\n")

        def work():
            try:
                with open(path, "rb") as f:
                    data = f.read()
                res = self._api_client().upload_file(
                    os.path.basename(path), data)
                txt = f"✅ Надіслано. Відповідь Moodle:\n{res}\n"
            except Exception as e:
                txt = f"❌ ПОМИЛКА: {e}\n"
            self.after(0, lambda: self.api_log.insert("end", txt))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------ COURSE TAB
    def _build_course_tab(self, root):
        top = ttk.Frame(root, padding=8)
        top.pack(fill="both", expand=True)

        # --- глобальні налаштування (1 раз на курс) ---
        gs = ttk.LabelFrame(top, text=" Глобальні налаштування тестування "
                            "(задаються 1 раз на весь курс) ", padding=6)
        gs.pack(fill="x", pady=4)
        ttk.Label(gs, text="Назва курсу:").grid(row=0, column=0, sticky="w")
        self.c_name = ttk.Entry(gs, width=30)
        self.c_name.insert(0, "Мій курс")
        self.c_name.grid(row=0, column=1, padx=4, sticky="we")
        ttk.Label(gs, text="Назва заняття:").grid(row=0, column=2, sticky="w")
        self.c_prefix = ttk.Combobox(gs, values=["Заняття", "Тема", "Тиждень",
                                                 "Модуль", "Урок"], width=10)
        self.c_prefix.set("Заняття")
        self.c_prefix.grid(row=0, column=3, padx=4, sticky="w")

        ttk.Label(gs, text="Час (хв, 0=без обмеж.):").grid(row=1, column=0,
                                                             sticky="w")
        self.c_time = ttk.Spinbox(gs, from_=0, to=600, width=6)
        self.c_time.set(0)
        self.c_time.grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(gs, text="Спроб (0=необмеж.):").grid(row=1, column=2,
                                                        sticky="w")
        self.c_attempts = ttk.Spinbox(gs, from_=0, to=10, width=6)
        self.c_attempts.set(0)
        self.c_attempts.grid(row=1, column=3, sticky="w", padx=4)

        ttk.Label(gs, text="Оцінювання:").grid(row=2, column=0, sticky="w")
        self.c_grading = ttk.Combobox(gs, values=["highest", "average",
                                                  "last", "first"],
                                      state="readonly", width=10)
        self.c_grading.set("highest")
        self.c_grading.grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(gs, text="Прохідний бал (%):").grid(row=2, column=2,
                                                       sticky="w")
        self.c_pass = ttk.Spinbox(gs, from_=0, to=100, width=6)
        self.c_pass.set(60)
        self.c_pass.grid(row=2, column=3, sticky="w", padx=4)

        self.c_shuffle = tk.BooleanVar(value=True)
        ttk.Checkbutton(gs, text="Перемішувати варіанти відповідей",
                        variable=self.c_shuffle).grid(row=3, column=0,
                                                      columnspan=2,
                                                      sticky="w", pady=2)
        ttk.Label(gs, text="Випадкових питань у тесті (0 = усі за списком):"
                  ).grid(row=3, column=2, sticky="w")
        self.c_random = ttk.Spinbox(gs, from_=0, to=500, width=6)
        self.c_random.set(0)
        self.c_random.grid(row=3, column=3, sticky="w", padx=4)

        # --- список тем (щоб не вводити для кожного заняття окремо) ---
        tf = ttk.LabelFrame(top, text=" Список тем (по одній в рядок) — "
                            "підставляється в назву занять за порядком ",
                            padding=6)
        tf.pack(fill="x", pady=4)
        self.c_topics = tk.Text(tf, height=5, wrap="word",
                                font=("Consolas", 9))
        self.c_topics.pack(fill="x")
        ttk.Label(tf, foreground="#666",
                  text="Якщо заповнено — назва кожного заняття береться "
                       "з цього списку за порядком (1 рядок = 1 заняття), "
                       "інакше використовується назва файлу.",
                  wraplength=820, justify="left").pack(anchor="w")

        # --- формат виходу ---
        of = ttk.LabelFrame(top, text=" Формат вихідного файлу ", padding=6)
        of.pack(fill="x", pady=4)
        self.c_outfmt = tk.StringVar(value="mbz")
        ttk.Radiobutton(of, text="📦 Повний курс Moodle (.mbz) — "
                        "резервна копія курсу (секції + тести + журнал "
                        "оцінок), імпорт через Restore",
                        variable=self.c_outfmt, value="mbz").pack(anchor="w")
        ttk.Radiobutton(of, text="📄 Банк питань (Moodle XML) — "
                        "ієрархічні категорії, імпорт у банк питань",
                        variable=self.c_outfmt, value="xml").pack(anchor="w")
        ttk.Label(of, text="Режим перегляду (Review options):").pack(
            side="left", padx=(0, 4), pady=2)
        self.c_review = ttk.Combobox(
            of, values=["standard", "strict", "full"],
            state="readonly", width=10)
        self.c_review.set("standard")
        self.c_review.pack(side="left")

        # --- файли (drag-and-drop) ---
        ff = ttk.Frame(top)
        ff.pack(fill="x", pady=4)
        ttk.Button(ff, text="📂 Додати сирі файли…",
                   command=self.course_add_files).pack(side="left")
        ttk.Button(ff, text="📁 Додати папку з файлами",
                   command=self.course_add_folder).pack(side="left", padx=4)
        ttk.Button(ff, text="🗑 Очистити",
                   command=self.course_clear).pack(side="left", padx=4)
        self.course_files_lbl = ttk.Label(ff, text="Файлів: 0",
                                          foreground="#666")
        self.course_files_lbl.pack(side="left", padx=10)

        # зона drag-and-drop + список файлів курсу
        dz = ttk.LabelFrame(top, text=" Сирі файли курсу — перетягніть "
                            "файли/папки сюди (масове додавання) ",
                            padding=4)
        dz.pack(fill="both", expand=True, pady=4)
        self.course_listbox = tk.Listbox(
            dz, height=6, font=("Consolas", 9), activestyle="none",
            selectmode="extended")
        cscroll = ttk.Scrollbar(dz, orient="vertical",
                                command=self.course_listbox.yview)
        self.course_listbox.configure(yscrollcommand=cscroll.set)
        self.course_listbox.pack(side="left", fill="both", expand=True)
        cscroll.pack(side="right", fill="y")
        ttk.Label(dz, foreground="#0a7a0a",
                  text="⬇ Drop: .txt .doc .docx .xlsx .csv .html — "
                       "усі підтримувані формати",
                  font=("Segoe UI", 9, "bold")).pack(fill="x")
        self._setup_course_dnd()

        bf = ttk.Frame(top)
        bf.pack(pady=6)
        ttk.Button(bf, text="⚙ ЗГЕНЕРУВАТИ КУРС",
                   command=self.course_generate).pack(side="left", padx=4)
        ttk.Button(bf, text="📤 Експорт сирих файлів…",
                   command=self.course_export_raw).pack(side="left", padx=4)

        self.course_log = tk.Text(top, height=8, wrap="none",
                                  font=("Consolas", 9))
        self.course_log.pack(fill="both", expand=True, pady=4)

        self._course_files = []

    COURSE_EXT = (".txt", ".aiken", ".doc", ".docx", ".xlsx", ".xlsm",
                  ".csv", ".html", ".htm")

    def _course_add_path(self, p):
        if p not in self._course_files:
            self._course_files.append(p)
            self.course_listbox.insert("end", os.path.basename(p))
        self.course_files_lbl.configure(
            text=f"Файлів: {len(self._course_files)}")

    def _setup_course_dnd(self):
        """Drag-and-drop: перетягування файлів/папок курсів у список.
        Динамічний імпорт: якщо tkinterdnd2 недоступний — працюють
        звичайні кнопки «Додати файли/папку», програма не падає."""
        try:
            import importlib
            dnd = importlib.import_module("tkinterdnd2")
            lb = self.course_listbox
            lb.drop_target_register(dnd.DND_FILES)
            lb.dnd_bind("<<Drop>>", self._course_on_drop)
        except Exception:
            pass  # DnD недоступний — працюють кнопки «Додати…»

    def _course_on_drop(self, event):
        """Обробник drop: парсить рядок {шляхи з пробілами у фігурних
        дужках} і додає файли/папки (рекурсивно)."""
        raw = event.data or ""
        items, cur, depth = [], "", 0
        for ch in raw:
            if ch == "{":
                depth += 1
                if depth == 1:
                    cur = ""
                    continue
            if ch == "}":
                depth -= 1
                if depth == 0:
                    items.append(cur)
                    cur = ""
                    continue
            if ch == " " and depth == 0:
                if cur:
                    items.append(cur)
                    cur = ""
                continue
            cur += ch
        if cur:
            items.append(cur)
        added = 0
        for it in items:
            it = it.strip()
            if not it:
                continue
            if os.path.isdir(it):
                for r, _d, names in os.walk(it):
                    for nm in sorted(names):
                        if nm.lower().endswith(self.COURSE_EXT):
                            p = os.path.join(r, nm)
                            if p not in self._course_files:
                                self._course_add_path(p)
                                added += 1
            elif it.lower().endswith(self.COURSE_EXT):
                if it not in self._course_files:
                    self._course_add_path(it)
                    added += 1
        if added:
            self.course_log.insert(
                "end", f"📥 Перетягуванням додано файлів: {added}\n")
            self.course_log.see("end")

    def course_add_files(self):
        paths = filedialog.askopenfilenames(
            title="Оберіть сирі файли курсу (усі підтримувані формати)",
            filetypes=[("Усі підтримувані",
                        "*.txt *.aiken *.doc *.docx *.xlsx *.csv "
                        "*.html *.htm"),
                       ("Текстові / Aiken", "*.txt *.aiken"),
                       ("Word", "*.docx *.doc"),
                       ("Excel", "*.xlsx"),
                       ("CSV", "*.csv"),
                       ("HTML", "*.html *.htm"),
                       ("Усі файли", "*.*")])
        for p in paths:
            self._course_add_path(p)

    def course_add_folder(self):
        folder = filedialog.askdirectory(
            title="Оберіть папку з сирими файлами курсу")
        if not folder:
            return
        for root_, _d, names in os.walk(folder):
            for nm in sorted(names):
                if nm.lower().endswith(self.COURSE_EXT):
                    self._course_add_path(os.path.join(root_, nm))

    def course_clear(self):
        self._course_files.clear()
        self.course_listbox.delete(0, "end")
        self.course_files_lbl.configure(text="Файлів: 0")
        self.course_log.delete("1.0", "end")

    def course_export_raw(self):
        """Експорт сирих файлів: копіює обрані файли в папку, конвертуючи
        не-txt формати (docx/doc/xlsx/csv/html) у нормалізований Aiken-.txt
        через converter_core. Налаштування — ті самі, що для курсу."""
        if not self._course_files:
            messagebox.showinfo("Експорт", "Спочатку додайте файли.")
            return
        folder = filedialog.askdirectory(
            title="Куди зберегти конвертовані сирі файли (.txt Aiken)")
        if not folder:
            return
        _load_core()
        ok, skipped = 0, []
        for p in self._course_files:
            base = os.path.splitext(os.path.basename(p))[0]
            try:
                if p.lower().endswith((".txt", ".aiken")):
                    with open(p, "rb") as f:
                        raw = f.read()
                    try:
                        from converter_core import decode_bytes
                        text = decode_bytes(raw)
                    except Exception:
                        text = raw.decode("utf-8-sig", errors="replace")
                else:
                    text = to_aiken(parse_file(p))
                with open(os.path.join(folder, base + ".txt"), "w",
                          encoding="utf-8") as f:
                    f.write(text)
                ok += 1
            except Exception as e:
                skipped.append(f"{os.path.basename(p)}: {e}")
        msg = f"✅ Експортовано файлів: {ok} у\n{folder}"
        if skipped:
            msg += "\n\n⚠ Пропущено:\n  " + "\n  ".join(skipped)
        self.course_log.delete("1.0", "end")
        self.course_log.insert("1.0", msg)

    def course_generate(self):
        import threading
        if not self._course_files:
            messagebox.showinfo("Курс", "Спочатку додайте сирі файли курсу.")
            return
        from course_module import GlobalSettings
        settings = GlobalSettings(
            course_name=self.c_name.get().strip() or "Курс",
            period_prefix=self.c_prefix.get().strip() or "Заняття",
            time_limit=int(self.c_time.get() or 0),
            attempts=int(self.c_attempts.get() or 0),
            grading_method=self.c_grading.get(),
            pass_percent=int(self.c_pass.get() or 60),
            shuffle_answers=self.c_shuffle.get(),
            random_questions=int(self.c_random.get() or 0))

        # список тем (1 рядок = 1 заняття) — переозначає назви файлів
        topics = [t.strip() for t in
                  self.c_topics.get("1.0", "end").splitlines() if t.strip()]

        out_fmt = self.c_outfmt.get()          # "mbz" | "xml"
        review = self.c_review.get() or "standard"

        if out_fmt == "mbz":
            path = filedialog.asksaveasfilename(
                defaultextension=".mbz",
                initialfile=(settings.course_name.replace(" ", "_")
                             + ".mbz"),
                filetypes=[("Moodle Backup", "*.mbz"),
                           ("ZIP-архів", "*.zip")])
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=".xml",
                initialfile="moodle_course_bank.xml",
                filetypes=[("Moodle XML", "*.xml")])
        if not path:
            return

        self.course_log.delete("1.0", "end")
        self.course_log.insert("end",
                               f"⏳ Генерація курсу ({out_fmt.upper()})...\n")

        def work():
            try:
                if out_fmt == "mbz":
                    from mbz_module import build_mbz_from_files
                    report = build_mbz_from_files(
                        self._course_files, settings, path,
                        topic_overrides=topics,
                        course_fullname=settings.course_name,
                        review_preset=review)
                    txt = (f"✅ Повний курс Moodle збережено: "
                           f"{os.path.basename(path)}\n\n" + report
                           + "\n\nІмпорт у Moodle: Адміністрування курсу → "
                             "Відновити (Restore) → оберіть .mbz")
                else:
                    from course_module import MoodleCourseGenerator
                    gen = MoodleCourseGenerator(settings)
                    xml_str, report = gen.generate(self._course_files,
                                                   topic_overrides=topics)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(xml_str)
                    txt = (f"✅ Банк питань збережено: "
                           f"{os.path.basename(path)}\n\n" + report)
            except Exception as e:
                txt = f"❌ ПОМИЛКА: {e}"
            self.after(0, lambda: (self.course_log.delete("1.0", "end"),
                                   self.course_log.insert("1.0", txt)))
        threading.Thread(target=work, daemon=True).start()

    # ------------------------------------------------------------- actions
    SUPPORTED_EXT = (".txt", ".doc", ".docx", ".xlsx", ".xlsm",
                     ".csv", ".html", ".htm")

    def _add_path(self, p):
        if p not in self.files:
            self.files.append(p)
            self.listbox.insert("end", os.path.basename(p))
        self.status_var.set(f"Додано файлів: {len(self.files)}")

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Оберіть файли тестів",
            filetypes=[("Усі підтримувані",
                        "*.txt *.doc *.docx *.xlsx *.csv *.html *.htm"),
                       ("Текстові", "*.txt"),
                       ("Word", "*.docx *.doc"),
                       ("Excel", "*.xlsx"),
                       ("CSV", "*.csv"),
                       ("HTML", "*.html *.htm"),
                       ("Усі файли", "*.*")])
        for p in paths:
            self._add_path(p)

    def add_folder(self):
        """Batch: add every supported file from a folder (recursively)."""
        folder = filedialog.askdirectory(
            title="Оберіть папку з файлами тестів")
        if not folder:
            return
        found = []
        for root, _dirs, names in os.walk(folder):
            for nm in sorted(names):
                if nm.lower().endswith(self.SUPPORTED_EXT):
                    found.append(os.path.join(root, nm))
        if not found:
            messagebox.showinfo(
                "Папка порожня",
                "У вибраній папці немає підтримуваних файлів\n"
                f"({', '.join(self.SUPPORTED_EXT)}).")
            return
        for p in found:
            self._add_path(p)
        messagebox.showinfo(
            "Папку додано",
            f"Знайдено і додано {len(found)} файлів з папки:\n{folder}")

    def clear_files(self):
        self.files.clear()
        self.listbox.delete(0, "end")
        self.preview.delete("1.0", "end")

    def _selected_path(self):
        sel = self.listbox.curselection()
        if sel:
            return self.files[sel[0]]
        return self.files[0] if self.files else None

    def preview_file(self):
        path = self._selected_path()
        if not path:
            messagebox.showinfo("Перегляд", "Спочатку додайте файл.")
            return
        _load_core()
        fmt, _ = FORMATS[self.fmt_var.get()]
        cat = self.cat_var.get().strip()
        single = self.single_var.get() == "single"
        self.preview.delete("1.0", "end")
        try:
            qs = parse_file(path)
            if single:
                from converter_core import force_single_answer
                force_single_answer(qs)
            # 'name:' header of a newTem; dump becomes the category
            if not cat and qs:
                cat = getattr(qs[0], "_topic", "") or ""
            head = f"Файл: {os.path.basename(path)}\nЗнайдено питань: {len(qs)}\n"
            for q in qs:
                corr = sum(1 for a in q.answers if a.correct)
                head += f"  [{q.qtype}] {q.text[:70]}  (правильних: {corr})\n"
            head += "\n" + "─" * 60 + "\n\n"
            if fmt == "gift":
                body = to_gift(qs, cat)
            elif fmt == "aiken":
                body = to_aiken(qs)
            else:
                body = to_moodle_xml(qs, cat)
            self.preview.insert("1.0", head + body)
        except Exception as e:
            self.preview.insert("1.0", f"ПОМИЛКА: {e}")

    def convert_all(self):
        if not self.files:
            messagebox.showinfo("Конвертація", "Додайте хоча б один файл.")
            return
        _load_core()
        fmt, ext = FORMATS[self.fmt_var.get()]
        cat = self.cat_var.get().strip()
        single = self.single_var.get() == "single"
        outdir = filedialog.askdirectory(title="Куди зберегти результати?")
        if not outdir:
            return

        # ---- fool-protection pre-flight checks -----------------------------
        problems = []
        for path in self.files:
            if not os.path.isfile(path):
                problems.append(f"файл не існує: {os.path.basename(path)}")
            elif not path.lower().endswith(self.SUPPORTED_EXT):
                problems.append(
                    f"непідтримуваний формат: {os.path.basename(path)}")
        if problems:
            if not messagebox.askyesno(
                    "Попередження",
                    "Виявлено проблемні файли:\n\n" + "\n".join(problems[:10])
                    + "\n\nПродовжити з рештою файлів?"):
                return
            self.files = [p for p in self.files
                          if os.path.isfile(p)
                          and p.lower().endswith(self.SUPPORTED_EXT)]
            self.listbox.delete(0, "end")
            for p in self.files:
                self.listbox.insert("end", os.path.basename(p))
            if not self.files:
                return

        # ---- batch conversion in a worker thread (GUI stays responsive) ---
        self.convert_btn.configure(state="disabled")
        self.progress.configure(maximum=len(self.files), value=0)
        log = []
        ok = 0

        def worker():
            nonlocal ok
            for i, path in enumerate(self.files, 1):
                base = os.path.splitext(os.path.basename(path))[0]
                out = os.path.join(outdir, base + ext)
                try:
                    qs = parse_file(path)
                    if not qs:
                        raise ValueError(
                            "питань не знайдено — перевірте розмітку\n"
                            "(можливо, у файлі не позначено правильні "
                            "відповіді)")
                    if single:
                        from converter_core import force_single_answer
                        force_single_answer(qs)
                    # per-file category: 'name:' header overrides default
                    file_cat = cat or getattr(qs[0], "_topic", "") or ""
                    if fmt == "gift":
                        content = to_gift(qs, file_cat)
                    elif fmt == "aiken":
                        skipped = len(qs) - len([
                            q for q in qs
                            if q.qtype == "multichoice"
                            and sum(1 for a in q.answers if a.correct) == 1])
                        content = to_aiken(qs)
                        if skipped:
                            log.append(
                                f"  ⚠ {os.path.basename(path)}: Aiken "
                                f"пропустив {skipped} питань (лише "
                                f"одна правильна відповідь)")
                    else:
                        content = to_moodle_xml(qs, file_cat)
                    with open(out, "w", encoding="utf-8") as f:
                        f.write(content)
                    log.append(
                        f"✔ {os.path.basename(path)} → "
                        f"{os.path.basename(out)}  ({len(qs)} питань)")
                    ok += 1
                except MemoryError:
                    log.append(f"✘ {os.path.basename(path)}: файл завеликий")
                except Exception as e:
                    log.append(f"✘ {os.path.basename(path)}: {e}")
                finally:
                    # update progress bar safely from the worker thread
                    self.after(0, self.progress.configure, {"value": i})
                    self.after(0, self.status_var.set,
                               f"Обробка {i}/{len(self.files)}: "
                               f"{os.path.basename(path)}")
            self.after(0, finish)

        def finish():
            self.convert_btn.configure(state="normal")
            self.status_var.set(
                f"Готово: {ok} з {len(self.files)} файлів")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", "\n".join(log))
            messagebox.showinfo(
                "Готово",
                f"Конвертовано {ok} з {len(self.files)} файлів.\n"
                f"Тека: {outdir}")

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def show_help(self):
        win = tk.Toplevel(self)
        win.title("Довідка — формати позначення")
        win.geometry("640x560")
        t = tk.Text(win, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
        t.insert("1.0", HELP_TEXT)
        t.configure(state="disabled")
        t.pack(fill="both", expand=True)

    def show_about(self):
        win = tk.Toplevel(self)
        win.title("Інформація — ліцензійна угода")
        win.geometry("660x600")
        t = tk.Text(win, wrap="word", font=("Segoe UI", 10), padx=10, pady=10)
        t.insert("1.0", ABOUT_TEXT)
        t.configure(state="disabled")
        t.pack(fill="both", expand=True)
        ttk.Button(win, text="Зрозуміло", command=win.destroy).pack(pady=8)


def run_cli(argv):
    """CLI mode: converter input1 [input2...] --format gift|xml|aiken
       [--category NAME] [--outdir DIR]"""
    import argparse
    ap = argparse.ArgumentParser(
        prog="MoodleTestConverter",
        description="Конвертер файлів тестів у формати Moodle (GIFT/XML/Aiken)")
    ap.add_argument("inputs", nargs="+", help="Вхідні файли тестів")
    ap.add_argument("--format", choices=["gift", "xml", "aiken"],
                    default="gift")
    ap.add_argument("--category", default="")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--single", action="store_true",
                    help="Одна правильна відповідь (лише перша позначена)")
    args = ap.parse_args(argv)

    _load_core()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    ext = {"gift": ".txt", "xml": ".xml", "aiken": ".txt"}[args.format]
    os.makedirs(args.outdir, exist_ok=True)
    for path in args.inputs:
        try:
            qs = parse_file(path)
            if not qs:
                raise ValueError("питань не знайдено")
            if args.single:
                from converter_core import force_single_answer
                force_single_answer(qs)
            if args.format == "gift":
                content = to_gift(qs, args.category)
            elif args.format == "aiken":
                content = to_aiken(qs)
            else:
                content = to_moodle_xml(qs, args.category)
            base = os.path.splitext(os.path.basename(path))[0]
            out = os.path.join(args.outdir, base + ext)
            with open(out, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"OK  {path} -> {out}  ({len(qs)} питань)")
        except Exception as e:
            print(f"FAIL {path}: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli(sys.argv[1:])
    else:
        App().mainloop()
