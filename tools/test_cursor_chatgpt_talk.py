#!/usr/bin/env python3
"""Prove Cursor and ChatGPT can exchange more than one turn with shared context."""

from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cursor_chatgpt_talk as talk


class RecordingHandler(BaseHTTPRequestHandler):
    requests: list[dict] = []

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode("utf-8"))
        self.requests.append(
            {
                "path": self.path,
                "authorization": self.headers.get("Authorization"),
                "payload": payload,
            }
        )
        user_turns = [m for m in payload["messages"] if m["role"] == "user"]
        if len(user_turns) == 1:
            reply = "I hear Cursor. Which page should we revise first?"
        else:
            reply = (
                "Continuing from that: start with the contact page, "
                "then send me the next note."
            )
        body = json.dumps(
            {"choices": [{"message": {"role": "assistant", "content": reply}}]}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        return


class TalkTests(unittest.TestCase):
    def test_parse_chatgpt_replies_keeps_each_turn(self) -> None:
        page = """
You said:
Hello from Cursor.
ChatGPT said:
PINE-THREAD
What should we work on?
You said:
Continue with the contact page.
ChatGPT said:
PINE-THREAD
What should change on the contact page?
ChatGPT is AI and can make mistakes.
"""
        replies = talk.parse_chatgpt_replies(page)
        self.assertEqual(
            replies,
            [
                "PINE-THREAD\nWhat should we work on?",
                "PINE-THREAD\nWhat should change on the contact page?",
            ],
        )

    def test_two_turns_keep_shared_context(self) -> None:
        RecordingHandler.requests = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), RecordingHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        base_url = f"http://{host}:{port}/v1"
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)

        with TemporaryDirectory() as tmp:
            thread_path = Path(tmp) / "thread.json"
            common = [
                "--thread",
                str(thread_path),
                "--base-url",
                base_url,
                "--model",
                "chat-latest",
            ]
            env_key = "test-key"
            import os

            previous = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = env_key
            self.addCleanup(self._restore_key, previous)

            first = talk.main(common + ["send", "Hello from Cursor. What should we work on first?"])
            second = talk.main(
                common
                + ["send", "--text", "Use the contact page and name the next step."]
            )
            shown = talk.main(common + ["show"])

            self.assertEqual(first, 0)
            self.assertEqual(second, 0)
            self.assertEqual(shown, 0)
            saved = json.loads(thread_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [m["role"] for m in saved["messages"]],
                ["cursor", "chatgpt", "cursor", "chatgpt"],
            )
            self.assertIn("contact page", saved["messages"][3]["content"].lower())
            self.assertNotIn(env_key, thread_path.read_text(encoding="utf-8"))

            self.assertEqual(len(RecordingHandler.requests), 2)
            second_payload = RecordingHandler.requests[1]["payload"]
            roles = [m["role"] for m in second_payload["messages"]]
            self.assertEqual(roles, ["developer", "user", "assistant", "user"])
            self.assertIn("Hello from Cursor", second_payload["messages"][1]["content"])
            self.assertIn("Which page", second_payload["messages"][2]["content"])
            self.assertIn("contact page", second_payload["messages"][3]["content"])
            self.assertEqual(
                RecordingHandler.requests[0]["authorization"],
                "Bearer test-key",
            )

            self.assertEqual(talk.main(common + ["reset"]), 0)
            self.assertFalse(thread_path.exists())

    def test_failed_reply_does_not_save_a_turn(self) -> None:
        class FailHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = b'{"error":{"message":"nope"}}'
                self.send_response(401)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt: str, *args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), FailHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        host, port = server.server_address

        with TemporaryDirectory() as tmp:
            thread_path = Path(tmp) / "thread.json"
            import os

            previous = os.environ.get("OPENAI_API_KEY")
            os.environ["OPENAI_API_KEY"] = "test-key"
            self.addCleanup(self._restore_key, previous)
            code = talk.main(
                [
                    "--thread",
                    str(thread_path),
                    "--base-url",
                    f"http://{host}:{port}/v1",
                    "send",
                    "Hello from Cursor.",
                ]
            )
            self.assertEqual(code, 1)
            self.assertFalse(thread_path.exists())

    def test_missing_key_exits_before_writing(self) -> None:
        import os

        previous = os.environ.pop("OPENAI_API_KEY", None)
        self.addCleanup(self._restore_key, previous)
        with TemporaryDirectory() as tmp:
            thread_path = Path(tmp) / "thread.json"
            code = talk.main(["--thread", str(thread_path), "send", "Hello"])
            self.assertEqual(code, 2)
            self.assertFalse(thread_path.exists())

    @staticmethod
    def _restore_key(previous: str | None) -> None:
        import os

        if previous is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = previous


if __name__ == "__main__":
    raise SystemExit(unittest.main())
