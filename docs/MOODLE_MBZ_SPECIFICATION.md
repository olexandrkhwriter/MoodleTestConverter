# Специфікація формату резервної копії курсу Moodle (.mbz)

> **Версія специфікації:** Moodle 2.0 – 4.5+ (Moodle Backup 2.x Schema)  
> **Перевірено на реальному бекапі:** Moodle 4.5.2 (Build: 20250210), курс IFNMU  
> **Тип файлу:** **TAR-архів, стиснений GZIP (`tar.gz`)**, зі службовим індексом `.ARCHIVE_INDEX`  
> **Призначення:** Відновлення та імпорт курсів через Web UI (`Restore`) або Moodle CLI.

---

## 1. Загальні вимоги до контейнера

1. **Тип архіву:** `.mbz` — це **GZIP-стиснений TAR** (сигнатура `1F 8B`, НЕ `PK`). Moodle НЕ приймає zip-контейнер як `.mbz`.
2. **`.ARCHIVE_INDEX`:** перший файл у TAR. Формат:
   ```
   Moodle archive file index. Count: <N>
   <шлях>\t<тип f|d>\t<розмір байт>\t<mtime unix>
   ```
   Директорії мають тип `d`, розмір `0`, mtime `?`.
3. **Кореневий рівень:** Усі кореневі XML-файли (`moodle_backup.xml`, `questions.xml` тощо) та службові папки (`course/`, `sections/`, `activities/`) **повинні знаходитися безпосередньо в корені архіву**.
   * *Заборонено:* створювати всередині TAR додаткову кореневу папку-обгортку.
4. **Кодування:** Усі XML-файли — `UTF-8` без BOM.
5. **Екранування даних:** XML-екранування (`&amp;`, `&lt;`, `&gt;`, `&apos;`, `&quot;`) або `<![CDATA[...]]>`. HTML-вміст всередині XML-полів (summary, intro, questiontext з `<p>`) екранується повністю (`&lt;p&gt;`).
6. **Шляхи в архіві:** лише ASCII (кириличні назви файлів не використовуються як шляхи).
7. **NULL-плейсхолдер:** порожні поля БД Moodle позначаються `$@NULL@$`.

---

## 2. Ієрархія файлової системи всередині .mbz

```text
/
├── .ARCHIVE_INDEX                 # Службовий індекс TAR (обов'язково першим!)
├── moodle_backup.xml              # Головний маніфест бекапу (індекс елементів та налаштування)
├── moodle_backup.log              # Лог створення бекапу (може бути порожнім)
├── questions.xml                  # Банк питань (категорії, питання, варіанти відповідей)
├── gradebook.xml                  # Журнал оцінок (категорії, формули, елементи оцінювання)
├── files.xml                      # Реєстр вкладених медіафайлів (зображення, вкладення)
├── groups.xml                     # Структура груп та групувань
├── outcomes.xml                   # Результати навчання (Outcomes/Competencies)
├── roles.xml                      # Визначення глобальних ролей бекапу
├── scales.xml                     # Користувацькі шкали оцінювання
├── badges.xml                     # Значки (badges)
├── completion.xml                 # Стан завершення курсу (course_completion)
├── grade_history.xml              # Історія оцінок
├── users.xml                      # Користувачі (якщо бекап з user data)
│
├── course/                        # Метадані курсу
│   ├── course.xml                 # Основні параметри курсу (назва, формат, дати)
│   ├── enrolments.xml             # Методи зарахування на курс
│   ├── inforef.xml                # Зовнішні залежності курсу (question_categoryref)
│   ├── roles.xml                  # Локальні ролі на рівні курсу
│   ├── filters.xml                # Активні фільтри курсу
│   ├── comments.xml               # Коментарі
│   ├── calendar.xml               # Події календаря
│   ├── contentbank.xml            # Банк H5P-контенту
│   ├── completiondefaults.xml     # Типові налаштування завершення
│   └── competencies.xml           # Компетентності курсу
│
├── sections/                      # Секції (Розділи / Теми / Тижні)
│   ├── section_1/                 # Нульова секція (Загальне / General)
│   │   ├── section.xml            # Параметри секції (номер, назва, послідовність)
│   │   └── inforef.xml            # У реальному бекапі 4.5 — порожній <inforef/>
│   └── section_{N}/               # Навчальні секції (Тема 1, Тема 2...)
│       ├── section.xml
│       └── inforef.xml
│
└── activities/                    # Модулі курсу (Тести, завдання, сторінки тощо)
    └── quiz_{moduleId}/           # Окремий модуль тестування (Quiz)
        ├── module.xml             # Метадані модуля (видимість, completion, секція)
        ├── quiz.xml               # Налаштування тесту, question_instance, фідбеки
        ├── inforef.xml            # Зв'язок тесту з Question Category IDs
        ├── grades.xml             # Налаштування оцінювання елемента
        ├── roles.xml              # Локальні перевизначення ролей для тесту
        ├── filters.xml            # Фільтри модуля
        ├── grade_history.xml      # Історія оцінок модуля
        ├── completion.xml         # Завершення модуля
        ├── comments.xml           # Коментарі модуля
        ├── calendar.xml           # Події календаря модуля
        ├── xapistate.xml          # Стан xAPI (H5P)
        └── competencies.xml       # Компетентності модуля
```

---

## 3. Матриця зв'язків ідентифікаторів (ID Mapping)

Для успішного імпорту значення первинних (`PK`) та зовнішніх (`FK`) ключів мають бути суворо узгоджені між різними XML-файлами:

| Сутність | Значення / Діапазон | Де декларується (PK) | Де використовується (FK) |
| :--- | :--- | :--- | :--- |
| **System Context ID** | `1` | Системне значення за замовчуванням | `moodle_backup.xml` |
| **Course Context ID** | `10` | `moodle_backup.xml` | `course/course.xml`, `questions.xml` |
| **Course ID** | `2` | `course/course.xml` (`id="2"`) | `moodle_backup.xml`, `gradebook.xml` |
| **Section DB ID** | `1` (загальне), `2..N` | `sections/section_{id}/section.xml` | `moodle_backup.xml`, `activities/quiz_{id}/module.xml` |
| **Section Number** | `0` (загальне), `1..N` | `sections/section_{id}/section.xml` | `activities/quiz_{id}/module.xml` |
| **Module ID** | `1..N` | `activities/quiz_{id}/module.xml` | `moodle_backup.xml`, `sections/section_{id}/section.xml` (`<sequence>`), `sections/section_{id}/inforef.xml` |
| **Category ID** | `1` (top), `2..N` | `questions.xml` (`<question_category id="...">`) | `course/inforef.xml`, `activities/quiz_{id}/inforef.xml`, `activities/quiz_{id}/quiz.xml` (`<slot>`) |
| **Question ID** | `1001..N` | `questions.xml` (`<question id="...">`) | `activities/quiz_{id}/quiz.xml` (`<slot>`), `activities/quiz_{id}/inforef.xml` (`<question>`) |
| **Answer ID** | `10001..N` | `questions.xml` (`<answer id="...">`) | Локально всередині `<question>` в `questions.xml` |
| **Grade Item ID** | `1` (курс), `2..N` (модулі) | `gradebook.xml` (`<grade_item id="...">`) | `activities/quiz_{id}/grades.xml` |

---

## 4. Специфікація та схема XML-файлів

### 4.1. `moodle_backup.xml`
Головний координаційний файл резервної копії.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<moodle_backup>
  <information>
    <name>backup-moodle2-course.mbz</name>
    <moodle_version>2022041900</moodle_version>
    <moodle_release>4.0</moodle_release>
    <backup_version>2022041900</backup_version>
    <backup_release>4.0</backup_release>
    <backup_date>1700000000</backup_date>
    <mnet_remoteusers>0</mnet_remoteusers>
    <include_files>0</include_files>
    <include_file_references_to_external_content>0</include_file_references_to_external_content>
    <original_wwwroot>http://localhost</original_wwwroot>
    <original_site_identifier_hash>mbzhash</original_site_identifier_hash>
    <original_course_id>2</original_course_id>
    <original_course_fullname>Повна назва курсу</original_course_fullname>
    <original_course_shortname>SHORT_NAME</original_course_shortname>
    <original_course_startdate>1700000000</original_course_startdate>
    <original_course_enddate>0</original_course_enddate>
    <original_course_contextid>10</original_course_contextid>
    <original_system_contextid>1</original_system_contextid>
    <details>
      <detail backup_id="mbz_1700000000">
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
        <activity>
          <moduleid>1</moduleid>
          <sectionid>2</sectionid>
          <modulename>quiz</modulename>
          <title>Тест: Тема 1</title>
          <directory>activities/quiz_1</directory>
        </activity>
      </activities>
      <sections>
        <section>
          <sectionid>1</sectionid>
          <title>Загальне</title>
          <directory>sections/section_1</directory>
        </section>
        <section>
          <sectionid>2</sectionid>
          <title>Тема 1: Основи</title>
          <directory>sections/section_2</directory>
        </section>
      </sections>
      <course>
        <courseid>2</courseid>
        <title>Повна назва курсу</title>
        <directory>course</directory>
      </course>
    </contents>
    <settings>
      <setting><level>root</level><name>filename</name><value>backup.mbz</value></setting>
      <setting><level>root</level><name>activities</name><value>1</value></setting>
      <setting><level>root</level><name>blocks</name><value>0</value></setting>
      <setting><level>root</level><name>filters</name><value>0</value></setting>
      <setting><level>root</level><name>comments</name><value>0</value></setting>
      <setting><level>root</level><name>badges</name><value>0</value></setting>
      <setting><level>root</level><name>calendarevents</name><value>0</value></setting>
      <setting><level>root</level><name>users</name><value>0</value></setting>
      <setting><level>root</level><name>questionbank</name><value>1</value></setting>
      <setting><level>root</level><name>groups</name><value>0</value></setting>
      <!-- Налаштування для кожної секції -->
      <setting><level>section</level><section>section_1</section><name>section_1_included</name><value>1</value></setting>
      <setting><level>section</level><section>section_1</section><name>section_1_userinfo</name><value>0</value></setting>
      <setting><level>section</level><section>section_2</section><name>section_2_included</name><value>1</value></setting>
      <setting><level>section</level><section>section_2</section><name>section_2_userinfo</name><value>0</value></setting>
      <!-- Налаштування для кожного модуля -->
      <setting><level>activity</level><activity>quiz_1</activity><name>quiz_1_included</name><value>1</value></setting>
      <setting><level>activity</level><activity>quiz_1</activity><name>quiz_1_userinfo</name><value>0</value></setting>
    </settings>
  </information>
</moodle_backup>
```

---

### 4.2. `course/`

#### `course/course.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<course id="2" contextid="10">
  <shortname>SHORT_NAME</shortname>
  <fullname>Повна назва курсу</fullname>
  <idnumber></idnumber>
  <summary>&lt;p&gt;Опис курсу&lt;/p&gt;</summary>
  <summaryformat>1</summaryformat>
  <format>topics</format>
  <showgrades>1</showgrades>
  <newsitems>5</newsitems>
  <startdate>1700000000</startdate>
  <enddate>0</enddate>
  <numsections>1</numsections>
  <enablecompletion>1</enablecompletion>
</course>
```

#### `course/inforef.xml`
Містить посилання на всі категорії банку питань, які належать цьому курсу:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<inforef>
  <question_category>
    <category><id>1</id></category>
    <category><id>2</id></category>
  </question_category>
</inforef>
```

#### `course/enrolments.xml` та `course/roles.xml`
```xml
<!-- course/enrolments.xml -->
<?xml version="1.0" encoding="UTF-8"?><enrolments><enrols></enrols></enrolments>

<!-- course/roles.xml -->
<?xml version="1.0" encoding="UTF-8"?><roles><role_overrides></role_overrides><role_assignments></role_assignments></roles>
```

---

### 4.3. `sections/section_{id}/`

#### `sections/section_{id}/section.xml`
- `number`: порядковий номер (починаючи з `0` для Загального, `1`, `2`... для тем).
- `sequence`: **Критично!** Список `moduleid` через кому (наприклад, `1` або `1,2,3`). Якщо тег порожній, модулі не з'являться на сторінці курсу.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<section id="2">
  <number>1</number>
  <name>Тема 1: Основи</name>
  <summary>&lt;p&gt;Опис теми&lt;/p&gt;</summary>
  <summaryformat>1</summaryformat>
  <sequence>1</sequence>
  <visible>1</visible>
  <availabilityjson>$@NULL@$</availabilityjson>
  <timemodified>1700000000</timemodified>
</section>
```

#### `sections/section_{id}/inforef.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<inforef>
  <activity>
    <id>1</id>
  </activity>
</inforef>
```

---

### 4.4. `questions.xml`
Описує дерево категорій та самі питання. **З Moodle 4.x питання обгортаються
в `question_bank_entries → question_bank_entry → question_version → question_versions → questions`**
(трьохрівнева схема версіонування питань).

* Приклад структури множинного вибору (`multichoice`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<question_categories>
  <!-- Коренева категорія (Top) -->
  <question_category id="1">
    <name>top</name>
    <contextid>10</contextid>
    <contextlevel>50</contextlevel>
    <contextinstanceid>2</contextinstanceid>
    <info></info>
    <infoformat>0</infoformat>
    <stamp>cat+stamp+top</stamp>
    <parent>0</parent>
    <sortorder>0</sortorder>
    <idnumber>$@NULL@$</idnumber>
    <question_bank_entries>
    </question_bank_entries>
  </question_category>

  <!-- Категорія секції/теми -->
  <question_category id="2">
    <name>Тема 1 - Основи</name>
    <contextid>10</contextid>
    <contextlevel>50</contextlevel>
    <contextinstanceid>2</contextinstanceid>
    <info></info>
    <infoformat>1</infoformat>
    <stamp>cat+stamp+2</stamp>
    <parent>1</parent>
    <sortorder>1000</sortorder>
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
                <name>Тема 1 - Питання 1</name>
                <questiontext>Текст тестового запитання?</questiontext>
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
                      <answertext>Правильний варіант</answertext>
                      <answerformat>1</answerformat>
                      <fraction>1.0000000</fraction>
                      <feedback></feedback>
                      <feedbackformat>1</feedbackformat>
                    </answer>
                    <answer id="10002">
                      <answertext>Неправильний варіант</answertext>
                      <answerformat>1</answerformat>
                      <fraction>0.0000000</fraction>
                      <feedback></feedback>
                      <feedbackformat>1</feedbackformat>
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

**Примітка:** категорія кожного тесту може мати власний context рівня модуля
(`contextlevel=70`, `contextinstanceid=<moduleid>`) або спільний context курсу
(`contextlevel=50`, `contextinstanceid=<courseid>`) — обидва варіанти валідні.

---

### 4.5. `activities/quiz_{id}/`

#### `activities/quiz_{id}/module.xml`
Керує системними налаштуваннями модуля та відстеженням виконання (Activity Completion).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<module id="1" version="2022041900">
  <modulename>quiz</modulename>
  <sectionid>2</sectionid>
  <sectionnumber>1</sectionnumber>
  <idnumber></idnumber>
  <added>1700000000</added>
  <score>0</score>
  <indent>0</indent>
  <visible>1</visible>
  <visibleoncoursepage>1</visibleoncoursepage>
  <visibleold>1</visibleold>
  <groupmode>0</groupmode>
  <groupingid>0</groupingid>
  <!-- Activity Completion: 0 - вимкнено, 1 - вручну студентом, 2 - автоматично при виконанні умов -->
  <completion>2</completion>
  <completiongradeitemnumber>0</completiongradeitemnumber>
  <completionview>1</completionview>
  <completionexpected>0</completionexpected>
  <completionpassgrade>1</completionpassgrade>
  <showdescription>0</showdescription>
</module>
```

#### `activities/quiz_{id}/quiz.xml`
Містить конфігурацію тестування, бітові маски прав огляду, слоти питань та порогові фідбеки.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<activity id="1" moduleid="1" modulename="quiz" contextid="101">
  <quiz id="1">
    <name>Тест: Тема 1</name>
    <intro>&lt;p&gt;Інструкція до тесту&lt;/p&gt;</intro>
    <introformat>1</introformat>
    <timeopen>0</timeopen>
    <timeclose>0</timeclose>
    <timelimit>1200</timelimit>
    <overduehandling>autosubmit</overduehandling>
    <graceperiod>0</graceperiod>
    <preferredbehaviour>deferredfeedback</preferredbehaviour>
    <canredoquestions>0</canredoquestions>
    <attempts_number>2</attempts_number>
    <attemptonlast>0</attemptonlast>
    <grademethod>1</grademethod>
    <decimalpoints>2</decimalpoints>
    <questiondecimalpoints>-1</questiondecimalpoints>
    <!-- Бітові маски Review Options (Moodle 4.5: обов'язково reviewmaxmarks) -->
    <reviewattempt>69888</reviewattempt>
    <reviewcorrectness>4352</reviewcorrectness>
    <reviewmaxmarks>69888</reviewmaxmarks>
    <reviewmarks>4352</reviewmarks>
    <reviewspecificfeedback>4352</reviewspecificfeedback>
    <reviewgeneralfeedback>4352</reviewgeneralfeedback>
    <reviewrightanswer>4352</reviewrightanswer>
    <reviewoverallfeedback>4352</reviewoverallfeedback>
    <questionsperpage>1</questionsperpage>
    <navmethod>free</navmethod>
    <shuffleanswers>1</shuffleanswers>
    <sumgrades>1.00000</sumgrades>
    <grade>1.00000</grade>
    <timecreated>1700000000</timecreated>
    <timemodified>1700000000</timemodified>
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
    <!-- Moodle 4.x: question_instance замість застарілого <slot>.
         ФІКСОВАНЕ питання прив'язується через question_reference ->
         questionbankentryid (ID запису question_bank_entry у questions.xml).
         question_set_reference — лише для ВИПАДКОВИХ питань із категорії;
         його використання для звичайного тесту = порожній тест після Restore! -->
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
    <feedbacks>
      <feedback id="11">
        <feedbacktext>&lt;p&gt;Відмінно!&lt;/p&gt;</feedbacktext>
        <feedbacktextformat>1</feedbacktextformat>
        <mingrade>0.90000</mingrade>
        <maxgrade>2.00000</maxgrade>
      </feedback>
      <feedback id="12">
        <feedbacktext>&lt;p&gt;Зараховано.&lt;/p&gt;</feedbacktext>
        <feedbacktextformat>1</feedbacktextformat>
        <mingrade>0.60000</mingrade>
        <maxgrade>0.90000</maxgrade>
      </feedback>
      <feedback id="13">
        <feedbacktext>&lt;p&gt;Не складено.&lt;/p&gt;</feedbacktext>
        <feedbacktextformat>1</feedbacktextformat>
        <mingrade>0.00000</mingrade>
        <maxgrade>0.60000</maxgrade>
      </feedback>
    </feedbacks>
    <overrides>
    </overrides>
    <grades>
    </grades>
    <attempts>
    </attempts>
  </quiz>
</activity>
```

#### `activities/quiz_{id}/inforef.xml` (Критично!)
Містить прив'язку до категорій банку питань через `question_categoryref`
(у реальному бекапі 4.5 також можуть бути `userref`, `grade_itemref`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<inforef>
  <question_categoryref>
    <question_category>
      <id>2</id>
    </question_category>
  </question_categoryref>
</inforef>
```

#### `course/inforef.xml`
Аналогічно використовує `question_categoryref` з переліком усіх категорій курсу:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<inforef>
  <question_categoryref>
    <question_category><id>1</id></question_category>
    <question_category><id>2</id></question_category>
  </question_categoryref>
</inforef>
```

#### `activities/quiz_{id}/grades.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<activity_gradebook>
  <grade_items>
    <grade_item id="2">
      <categoryid>1</categoryid>
      <itemname>Тест: Тема 1</itemname>
      <itemtype>mod</itemtype>
      <itemmodule>quiz</itemmodule>
      <iteminstance>1</iteminstance>
      <itemnumber>0</itemnumber>
      <gradetype>1</gradetype>
      <grademax>1.00000</grademax>
      <grademin>0.00000</grademin>
      <gradepass>0.60000</gradepass>
      <timecreated>1700000000</timecreated>
      <timemodified>1700000000</timemodified>
    </grade_item>
  </grade_items>
  <grade_letters></grade_letters>
</activity_gradebook>
```

---

### 4.6. `gradebook.xml`
Описує підсумкову оцінку курсу та прив'язку всіх оцінюваних елементів (тестів).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<gradebook>
  <attributes>
  </attributes>
  <grade_categories>
    <grade_category id="1">
      <parent>$@NULL@$</parent>
      <depth>1</depth>
      <path>/1/</path>
      <fullname>?</fullname>
      <aggregation>13</aggregation>
      <keephigh>0</keephigh>
      <droplow>0</droplow>
      <aggregateonlygraded>1</aggregateonlygraded>
      <aggregateoutcomes>0</aggregateoutcomes>
      <timecreated>1700000000</timecreated>
      <timemodified>1700000000</timemodified>
      <hidden>0</hidden>
    </grade_category>
  </grade_categories>
  <grade_items>
    <!-- Підсумкова оцінка за весь курс -->
    <grade_item id="1">
      <categoryid>$@NULL@$</categoryid>
      <itemname>$@NULL@$</itemname>
      <itemtype>course</itemtype>
      <itemmodule>$@NULL@$</itemmodule>
      <iteminstance>2</iteminstance>
      <itemnumber>$@NULL@$</itemnumber>
      <gradetype>1</gradetype>
      <grademax>100.00000</grademax>
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
      <timecreated>1700000000</timecreated>
      <timemodified>1700000000</timemodified>
    </grade_item>
    <!-- Оцінка конкретного тесту -->
    <grade_item id="2">
      <categoryid>1</categoryid>
      <itemname>Тест: Тема 1</itemname>
      <itemtype>mod</itemtype>
      <itemmodule>quiz</itemmodule>
      <iteminstance>1</iteminstance>
      <itemnumber>0</itemnumber>
      <iteminfo>$@NULL@$</iteminfo>
      <idnumber></idnumber>
      <calculation>$@NULL@$</calculation>
      <gradetype>1</gradetype>
      <grademax>1.00000</grademax>
      <grademin>0.00000</grademin>
      <scaleid>$@NULL@$</scaleid>
      <outcomeid>$@NULL@$</outcomeid>
      <gradepass>0.60000</gradepass>
      <multfactor>1.00000</multfactor>
      <plusfactor>0.00000</plusfactor>
      <aggregationcoef>0.00000</aggregationcoef>
      <aggregationcoef2>0.00000</aggregationcoef2>
      <weightoverride>0</weightoverride>
      <sortorder>2</sortorder>
      <display>0</display>
      <decimals>$@NULL@$</decimals>
      <hidden>0</hidden>
      <locked>0</locked>
      <locktime>0</locktime>
      <needsupdate>0</needsupdate>
      <timecreated>1700000000</timecreated>
      <timemodified>1700000000</timemodified>
    </grade_item>
  </grade_items>
  <grade_letters>
  </grade_letters>
  <grade_settings>
  </grade_settings>
</gradebook>
```

---

### 4.7. Допоміжні XML-файли (Мінімальні обов'язкові шаблони)

```xml
<!-- files.xml -->
<?xml version="1.0" encoding="UTF-8"?><files></files>

<!-- groups.xml -->
<?xml version="1.0" encoding="UTF-8"?><groups></groups>

<!-- outcomes.xml -->
<?xml version="1.0" encoding="UTF-8"?><outcomes_definition></outcomes_definition>

<!-- scales.xml -->
<?xml version="1.0" encoding="UTF-8"?><scales_definition></scales_definition>

<!-- roles.xml -->
<?xml version="1.0" encoding="UTF-8"?><roles_definition></roles_definition>
```

---

## 5. Довідник значень параметрів тестування (Quiz Flags)

### 5.1. Бітові маски параметрів перегляду (Review Options)
Moodle кодує 4 часові інтервали доступу до інформації за допомогою бітових масок (DURING = 1, IMMEDIATELY = 16, OPEN = 256, CLOSED = 4096):

* **Стандартний безпечний режим (Standard):**
  * `reviewattempt`: `69888` (бачить спробу після закриття)
  * `reviewcorrectness`: `4352`
  * `reviewmarks`: `4352`
  * `reviewspecificfeedback`: `4352`
  * `reviewgeneralfeedback`: `4352`
  * `reviewrightanswer`: `4352`
  * `reviewoverallfeedback`: `4352`
* **Суворий режим (Strict — без показу правильних відповідей):**
  * `reviewcorrectness`: `0`
  * `reviewrightanswer`: `0`
  * `reviewspecificfeedback`: `0`
  * `reviewgeneralfeedback`: `0`
  * `reviewmarks`: `4352`
  * `reviewoverallfeedback`: `4352`
* **Повністю відкритий режим (Full):**
  * Усі значення встановлюються в `69904`.

### 5.2. Поведінка питань (`preferredbehaviour`)
* `deferredfeedback` — Відкладений відгук (найпоширеніший для екзаменів).
* `immediatefeedback` — Безпосередній відгук.
* `interactive` — Інтерактивний з кількома спробами.
* `adaptive` — Адаптивний режим (зі штрафами).
* `adaptivenopenalty` — Адаптивний режим без штрафів.

### 5.3. Метод оцінювання (`grademethod`)
* `1` — Найвища оцінка (Highest grade).
* `2` — Середня оцінка (Average grade).
* `3` — Перша спроба (First attempt).
* `4` — Остання спроба (Last attempt).

---

## 6. Чекліст валідації перед пакуванням

1. [ ] **Контейнер — TAR.GZ** (сигнатура `1F 8B`), НЕ zip. Перший запис у TAR — `.ARCHIVE_INDEX` із коректним `Count`.
2. [ ] Усі числові поля з дробовою частиною у `gradebook.xml` та `quiz.xml` (`grademax`, `gradepass`, `fraction`) форматовані з точністю до 5 або 7 знаків після коми (наприклад, `1.00000` або `0.3333333`).
3. [ ] `sequence` у кожній секції містить реальний ID активностей або залишається пустим для секцій без активностей.
4. [ ] `questions.xml`: питання обгорнуті в `question_bank_entries → question_bank_entry → question_version → question_versions → questions`; статус версії — `ready`.
5. [ ] `quiz.xml`: слоти оформлені як `question_instance` із вкладеним **`question_reference` → `questionbankentryid`** (для фіксованих питань) — НЕ `question_set_reference` (він лише для випадкових); `questionbankentryid` кожного слота відповідає реальному `question_bank_entry id` у `questions.xml`; присутнє `reviewmaxmarks`; наприкінці — порожні `<overrides>`, `<grades>`, `<attempts>`.
6. [ ] Відсутнє подвійне або невірне вкладення тегів у `inforef.xml` активностей.
7. [ ] Порожні поля бази даних Moodle замінені на `$@NULL@$`.
8. [ ] Шляхи в TAR — лише ASCII, без кореневої папки-обгортки.
9. [ ] Усі XML парсяться стандартним парсером (ElementTree) без помилок.
