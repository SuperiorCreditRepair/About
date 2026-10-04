#!/usr/bin/env python3
"""Keep a two-way conversation between Cursor and ChatGPT.

Cursor sends a turn. ChatGPT replies through the OpenAI Chat Completions API.
The next send includes the earlier turns, so the exchange continues with
shared context.

    set OPENAI_API_KEY=sk-...
    python tools/cursor_chatgpt_talk.py send "Hello from Cursor. What should we work on first?"
    python tools/cursor_chatgpt_talk.py send "Use that idea and name the next step."
    python tools/cursor_chatgpt_talk.py show
    python tools/cursor_chatgpt_talk.py reset

The thread is stored in chatgpt_bridge/thread.json and is not committed.
Set OPENAI_MODEL to override the default model (chat-latest, the current
ChatGPT instant model). Set OPENAI_BASE_URL to point at another
Chat Completions endpoint.

    python tools/cursor_chatgpt_talk.py --transport browser send "Hello from Cursor."

Browser mode uses the ChatGPT website in a Chrome window that is already
open with remote debugging on 127.0.0.1:9222. It does not need an API key.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MODEL = "chat-latest"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_THREAD = Path("chatgpt_bridge/thread.json")
DEFAULT_TIMEOUT = 120

INSTRUCTION = (
    "You are ChatGPT in a two-way working conversation with Cursor. "
    "Each user message is Cursor's next turn. Reply directly, use the "
    "earlier turns when they matter, and leave a clear opening for Cursor "
    "to answer you again."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_thread(model: str) -> dict:
    return {"model": model, "created_at": utc_now(), "messages": []}


def load_thread(path: Path, model: str) -> dict:
    if not path.exists():
        return empty_thread(model)
    thread = json.loads(path.read_text(encoding="utf-8"))
    thread.setdefault("messages", [])
    thread.setdefault("model", model)
    return thread


def save_thread(path: Path, thread: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(thread, indent=2) + "\n", encoding="utf-8")


def message_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(str(part.get("text") or ""))
        return "".join(parts)
    return ""


def to_api_messages(thread: dict) -> list[dict]:
    api_messages = [{"role": "developer", "content": INSTRUCTION}]
    for turn in thread["messages"]:
        role = "assistant" if turn["role"] == "chatgpt" else "user"
        api_messages.append({"role": role, "content": turn["content"]})
    return api_messages


class ChatGPTError(RuntimeError):
    pass


def request_reply(
    api_messages: list[dict],
    *,
    api_key: str,
    model: str,
    base_url: str,
    timeout: float,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "messages": api_messages}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ChatGPTError(f"ChatGPT HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ChatGPTError(f"ChatGPT request failed: {exc.reason}") from exc

    try:
        reply = message_text(payload["choices"][0]["message"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ChatGPTError(f"ChatGPT returned an unexpected payload: {payload}") from exc
    if not reply:
        raise ChatGPTError("ChatGPT returned an empty reply.")
    return reply


def append_exchange(thread: dict, cursor_text: str, reply: str, model: str) -> None:
    thread["model"] = model
    thread["updated_at"] = utc_now()
    thread["messages"].append(
        {"role": "cursor", "content": cursor_text, "at": thread["updated_at"]}
    )
    thread["messages"].append(
        {"role": "chatgpt", "content": reply, "at": thread["updated_at"]}
    )


def parse_chatgpt_replies(page_text: str) -> list[str]:
    replies: list[str] = []
    chunks = page_text.split("ChatGPT said:")[1:]
    for chunk in chunks:
        for marker in ("You said:", "ChatGPT is AI", "Chat with ChatGPT"):
            index = chunk.find(marker)
            if index >= 0:
                chunk = chunk[:index]
        text = "\n".join(line.strip() for line in chunk.splitlines() if line.strip())
        if text:
            replies.append(text)
    return replies


def _page_text_via_cdp(debug_port: int, timeout: float) -> tuple[object, str]:
    import websocket

    targets = json.load(
        urllib.request.urlopen(f"http://127.0.0.1:{debug_port}/json/list", timeout=10)
    )
    page = next(
        (
            target
            for target in targets
            if target.get("type") == "page" and "chatgpt.com" in target.get("url", "")
        ),
        None,
    )
    if page is None:
        raise ChatGPTError(
            "No chatgpt.com tab is open in Chrome on the debug port."
        )
    socket = websocket.create_connection(
        page["webSocketDebuggerUrl"],
        timeout=timeout,
        suppress_origin=True,
    )
    return socket, page["url"]


def _cdp(socket: object, method: str, params: dict | None = None, timeout: float = 30) -> dict:
    call_id = getattr(socket, "_cursor_cdp_id", 0) + 1
    setattr(socket, "_cursor_cdp_id", call_id)
    socket.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = json.loads(socket.recv())
        if data.get("id") == call_id:
            if "error" in data:
                raise ChatGPTError(f"Chrome debugger error: {data['error']}")
            return data["result"]
    raise ChatGPTError(f"Chrome debugger timed out during {method}.")


def browser_page_text(socket: object) -> str:
    result = _cdp(
        socket,
        "Runtime.evaluate",
        {
            "expression": "document.body ? document.body.innerText : ''",
            "returnByValue": True,
        },
    )
    return str(result.get("result", {}).get("value") or "")


def browser_send_message(socket: object, cursor_text: str) -> None:
    script = """
(() => {
  const el = document.querySelector('textarea');
  if (!el) return 'no textarea';
  const proto = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
  proto.set.call(el, TEXT);
  el.focus();
  el.dispatchEvent(new Event('input', {bubbles:true}));
  const btn = document.querySelector('button[aria-label="Send message"]');
  if (!btn) return 'no send button';
  btn.click();
  return 'sent';
})()
""".replace("TEXT", json.dumps(cursor_text))
    result = _cdp(
        socket,
        "Runtime.evaluate",
        {"expression": script, "returnByValue": True},
    )
    status = str(result.get("result", {}).get("value") or "")
    if status != "sent":
        raise ChatGPTError(f"Could not send the message in ChatGPT: {status}")


def request_browser_reply(cursor_text: str, *, debug_port: int, timeout: float) -> str:
    socket, _url = _page_text_via_cdp(debug_port, timeout)
    try:
        before = len(parse_chatgpt_replies(browser_page_text(socket)))
        browser_send_message(socket, cursor_text)
        deadline = time.monotonic() + timeout
        latest = ""
        stable = 0
        while time.monotonic() < deadline:
            time.sleep(1)
            replies = parse_chatgpt_replies(browser_page_text(socket))
            if len(replies) <= before:
                stable = 0
                continue
            current = replies[-1]
            if current == latest:
                stable += 1
                if stable >= 2:
                    return current
            else:
                latest = current
                stable = 0
        if latest:
            return latest
        raise ChatGPTError("ChatGPT did not reply in the open browser tab.")
    finally:
        socket.close()


def send_turn(
    thread: dict,
    cursor_text: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    timeout: float,
) -> str:
    text = cursor_text.strip()
    if not text:
        raise ChatGPTError("Cursor's message is empty.")
    pending = dict(thread)
    pending["messages"] = list(thread["messages"]) + [
        {"role": "cursor", "content": text, "at": utc_now()}
    ]
    reply = request_reply(
        to_api_messages(pending),
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=timeout,
    )
    append_exchange(thread, text, reply, model)
    return reply


def format_thread(thread: dict) -> str:
    lines = [f"model: {thread.get('model', '')}", ""]
    messages = thread.get("messages") or []
    if not messages:
        lines.append("(no turns yet)")
        return "\n".join(lines)
    for turn in messages:
        speaker = "Cursor" if turn["role"] == "cursor" else "ChatGPT"
        lines.append(f"{speaker}: {turn['content']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def read_message(args: argparse.Namespace) -> str:
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if args.text == "-":
        return sys.stdin.read()
    if args.text is not None:
        return args.text
    return " ".join(args.words)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Talk back and forth with ChatGPT.")
    parser.add_argument(
        "--thread",
        type=Path,
        default=Path(os.environ.get("CHATGPT_THREAD", DEFAULT_THREAD)),
    )
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL),
    )
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--transport",
        choices=("api", "browser"),
        default=os.environ.get("CHATGPT_TRANSPORT", "api"),
        help="api uses OPENAI_API_KEY. browser uses an open chatgpt.com tab.",
    )
    parser.add_argument(
        "--debug-port",
        type=int,
        default=int(os.environ.get("CHATGPT_DEBUG_PORT", "9222")),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="Send Cursor's next turn and print ChatGPT's reply.")
    send.add_argument("words", nargs="*", help="Message text. Omit when using --file or '-'.")
    send.add_argument("--file", help="Read Cursor's message from this file.")
    send.add_argument("--text", help="Message text. Use '-' to read stdin.")

    sub.add_parser("show", help="Print the saved conversation.")
    sub.add_parser("reset", help="Delete the saved conversation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "show":
        thread = load_thread(args.thread, args.model)
        sys.stdout.write(format_thread(thread))
        return 0
    if args.command == "reset":
        if args.thread.exists():
            args.thread.unlink()
        print(f"Cleared {args.thread}")
        return 0

    try:
        cursor_text = read_message(args).strip()
        if not cursor_text:
            raise ChatGPTError("Cursor's message is empty.")
        thread = load_thread(args.thread, args.model)
        if args.transport == "browser":
            reply = request_browser_reply(
                cursor_text,
                debug_port=args.debug_port,
                timeout=args.timeout,
            )
            append_exchange(thread, cursor_text, reply, "chatgpt.com")
        else:
            api_key = os.environ.get("OPENAI_API_KEY", "").strip()
            if not api_key:
                print(
                    "OPENAI_API_KEY is not set. Add a ChatGPT / OpenAI API key, then run send again.",
                    file=sys.stderr,
                )
                return 2
            reply = send_turn(
                thread,
                cursor_text,
                api_key=api_key,
                model=args.model,
                base_url=args.base_url,
                timeout=args.timeout,
            )
        save_thread(args.thread, thread)
    except (ChatGPTError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    sys.stdout.write(reply)
    if not reply.endswith("\n"):
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
