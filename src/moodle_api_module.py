# -*- coding: utf-8 -*-
"""
Модуль API-з'єднання з Moodle (Web Services / REST).
Дозволяє перевірити з'єднання, отримати список курсів і категорій питань,
а також експортувати/імпортувати контент (через webservice endpoints).

УВАГА: Moodle не має офіційного endpoint для прямого імпорту GIFT/XML
у банк питань. Цей модуль надає:
  • перевірку токена та отримання інформації про сайт/курси/категорії;
  • завантаження (upload) файлу у draft-область (core_files_upload);
  • виклик довільної WS-функції (для розширень/плагінів, якщо встановлено).
Для повноцінного автоімпорту питань у банк потрібен плагін
(наприклад, qformat REST) — модуль готовий до нього через call().
"""

import json
import urllib.parse
import urllib.request
import urllib.error


class MoodleAPIError(Exception):
    pass


class MoodleAPI:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base = base_url.rstrip("/")
        self.token = token.strip()
        self.timeout = timeout
        if not self.base.startswith("http"):
            raise MoodleAPIError(
                "URL Moodle має починатися з http:// або https://")

    # ------------------------------------------------------------ request
    def _endpoint(self):
        return f"{self.base}/webservice/rest/server.php"

    def call(self, function: str, **params):
        """Call any Moodle web-service function, return decoded JSON."""
        data = {"wstoken": self.token, "wsfunction": function,
                "moodlewsrestformat": "json"}
        data.update(params)
        body = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(self._endpoint(), data=body)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                out = json.loads(r.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise MoodleAPIError(f"Не вдалося з'єднатися з Moodle: {e}")
        if isinstance(out, dict) and "exception" in out:
            raise MoodleAPIError(
                f"Moodle: {out.get('message', out['exception'])}")
        return out

    # ------------------------------------------------------------ helpers
    def test_connection(self):
        """Return site info dict (sitename, username, version...)."""
        return self.call("core_webservice_get_site_info")

    def get_courses(self):
        return self.call("core_course_get_courses")

    def get_question_categories(self, course_id: int):
        # через зовнішню функцію (якщо доступна) — інакше помилка
        return self.call("core_question_get_categories",
                         courseid=int(course_id))

    def upload_file(self, filename: str, content: bytes,
                    contextid: int = 1, component="user",
                    filearea="draft", itemid=0):
        """Upload a file into a draft area (base64)."""
        import base64
        b64 = base64.b64encode(content).decode("ascii")
        return self.call("core_files_upload", contextid=contextid,
                         component=component, filearea=filearea,
                         itemid=itemid, filename=filename, filecontent=b64)
