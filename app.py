from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import re
import sqlite3

ROOT = Path(__file__).resolve().parent
EVENT_TYPES = {"form_opened", "application_submitted", "card_activated"}


def seed(db):
    sample = (ROOT / "sql/02_sample_data.sql").read_text(encoding="utf-8")
    with db:
        db.executescript("BEGIN; DELETE FROM application_events;\n" + sample + "\nCOMMIT;")


def snapshot(db):
    queries = {
        "counts": """SELECT status, COUNT(*) AS count FROM application_status
                     GROUP BY status""",
        "applications": "SELECT * FROM application_status ORDER BY application_id",
        "issues": "SELECT * FROM application_quality_issues ORDER BY application_id, issue",
        "events": "SELECT * FROM application_events ORDER BY event_id DESC",
    }
    return {name: [dict(row) for row in db.execute(query)] for name, query in queries.items()}


def record(db, payload):
    event_id = payload.get("event_id")
    if event_id is not None:
        if type(event_id) is not int or not 0 < event_id < 2**63:
            raise ValueError("Укажи корректный номер события.")
        db.execute(
            """INSERT INTO application_events
               SELECT * FROM application_events WHERE event_id = ?
               ON CONFLICT (event_id) DO NOTHING""",
            (event_id,),
        )
        if not db.execute("SELECT 1 FROM application_events WHERE event_id = ?", (event_id,)).fetchone():
            raise ValueError("Событие для повторной доставки не найдено.")
        return "Повторная доставка. Запись с таким номером уже есть в журнале."

    application_id = payload.get("application_id")
    event_type = payload.get("event_type")
    if not isinstance(application_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,24}", application_id):
        raise ValueError("В номере заявки используй до 24 латинских букв, цифр, дефисов или подчёркиваний.")
    if not isinstance(event_type, str) or event_type not in EVENT_TYPES:
        raise ValueError("Выбери тип события.")
    occurred_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f+00")
    db.execute(
        "INSERT INTO application_events (application_id, event_type, occurred_at) VALUES (?, ?, ?)",
        (application_id.upper(), event_type, occurred_at),
    )
    return "Событие записано."


def serve(db, port=8000):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, body, content_type):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, data, status=200):
            self.reply(status, json.dumps(data, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            if self.path == "/":
                self.reply(200, (ROOT / "web/index.html").read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/api/state":
                self.send_json(snapshot(db))
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path not in {"/api/events", "/api/reset"}:
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if self.headers.get_content_type() != "application/json" or not 0 < length <= 4096:
                    raise ValueError("Ожидается небольшой запрос в формате JSON.")
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError("Ожидается объект JSON.")
                if self.path == "/api/reset":
                    seed(db)
                    message = "Исходный набор восстановлен."
                else:
                    with db:
                        message = record(db, payload)
                self.send_json({**snapshot(db), "message": message})
            except (json.JSONDecodeError, UnicodeDecodeError):
                self.send_json({"error": "Некорректный JSON."}, 400)
            except ValueError as error:
                self.send_json({"error": str(error)}, 400)

    return HTTPServer(("127.0.0.1", port), Handler)


def create_database():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / "sql/01_schema.sql").read_text(encoding="utf-8"))
    seed(db)
    db.executescript((ROOT / "sql/03_report.sql").read_text(encoding="utf-8"))
    return db


if __name__ == "__main__":
    from argparse import ArgumentParser
    from contextlib import closing

    parser = ArgumentParser(description="Локальный демонстрационный стенд для учёта заявок")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with closing(create_database()) as db, serve(db, args.port) as server:
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
