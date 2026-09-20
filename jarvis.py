#!/usr/bin/env python3
"""JARVIS: a small, safe, terminal personal assistant.

The core uses only Python's standard library so it runs easily in Termux.
Optional integrations can be added behind the command router later.
"""

from __future__ import annotations

import ast
import datetime as dt
import operator
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "JARVIS"
DB_PATH = Path(os.environ.get("JARVIS_DB", Path.home() / ".jarvis" / "jarvis.db"))


class SafeCalculator:
    """Evaluate arithmetic without executing arbitrary Python code."""

    _binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    @classmethod
    def calculate(cls, expression: str) -> int | float:
        if len(expression) > 200:
            raise ValueError("expression is too long")
        try:
            tree = ast.parse(expression, mode="eval")
            result = cls._evaluate(tree.body)
        except (SyntaxError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
            raise ValueError("I can only calculate safe arithmetic expressions") from exc
        if isinstance(result, float) and not result.is_integer():
            return round(result, 10)
        return int(result) if isinstance(result, float) else result

    @classmethod
    def _evaluate(cls, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 10**100:
                raise ValueError("number is too large")
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in cls._binary_ops:
            left, right = cls._evaluate(node.left), cls._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("power is too large")
            return cls._binary_ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls._unary_ops:
            return cls._unary_ops[type(node.op)](cls._evaluate(node.operand))
        raise ValueError("unsupported expression")


class Memory:
    def __init__(self, path: Path = DB_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self.connection.commit()

    def remember(self, content: str) -> None:
        self.connection.execute(
            "INSERT INTO memories(content, created_at) VALUES (?, ?)",
            (content, dt.datetime.now(dt.timezone.utc).isoformat()),
        )
        self.connection.commit()

    def recent(self, limit: int = 10) -> list[str]:
        rows = self.connection.execute(
            "SELECT content FROM memories ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [row[0] for row in reversed(rows)]

    def close(self) -> None:
        self.connection.close()


@dataclass
class Response:
    text: str
    should_exit: bool = False


class Jarvis:
    def __init__(self) -> None:
        self.memory = Memory()

    def handle(self, raw: str) -> Response:
        text = " ".join(raw.strip().split())
        if not text:
            return Response("")
        command, _, argument = text.partition(" ")
        command = command.lower()

        if command in {"exit", "quit", "bye"}:
            return Response("Goodbye. Stay safe.", should_exit=True)
        if command in {"help", "?"}:
            return Response(self.help_text())
        if command in {"clear", "cls"}:
            return Response("__CLEAR__")
        if command in {"hello", "hi", "hey"}:
            return Response("Hello. How can I help you?")
        if command in {"time", "date"}:
            now = dt.datetime.now().astimezone()
            return Response(now.strftime("%A, %d %B %Y at %I:%M %p"))
        if command in {"calc", "calculate"}:
            if not argument:
                return Response("Usage: calculate 25 * 48")
            try:
                return Response(f"🧮 {argument} = {SafeCalculator.calculate(argument)}")
            except ValueError as exc:
                return Response(f"🔴 {exc}")
        if command in {"remember", "learn"}:
            if not argument:
                return Response("Usage: remember your note")
            self.memory.remember(argument)
            return Response("🧠 I will remember that.")
        if command in {"memory", "memories", "recall"}:
            notes = self.memory.recent()
            return Response("🧠 Memory is empty." if not notes else "🧠 Recent memory:\n" + "\n".join(f"• {n}" for n in notes))
        if command in {"ask", "chat"}:
            return Response("Gemini integration is not configured yet. Set it up behind the AI tool in the next step.")
        if command == "search":
            return Response("Search integration is not configured yet. Use an API-backed search tool when credentials are available.")
        if command == "weather":
            return Response("Weather integration is not configured yet. Please add a weather provider API.")
        return Response(f"I understood: {text}\nTry 'help' to see available commands.")

    @staticmethod
    def help_text() -> str:
        return """Commands:
  hello                         Greet JARVIS
  calculate 25 * 48             Safe arithmetic
  remember <text>               Save a note to SQLite
  memory                        Show saved notes
  time / date                   Show local date and time
  search <query>                Search placeholder
  weather <location>            Weather placeholder
  ask <question>                Gemini placeholder
  clear                         Clear the terminal
  help                          Show this help
  exit                          Quit JARVIS

Database: ~/.jarvis/jarvis.db (override with JARVIS_DB)"""


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def print_banner() -> None:
    print("─" * 58)
    print("                         J A R V I S")
    print("                    Personal AI Assistant")
    print("─" * 58)
    print("  🤖 System    ● Online")
    print("  🧠 Memory    ● Online")
    print("  ⚙️  Engine    ● Ready")
    print("─" * 58)
    print("Type 'help' for commands, or 'exit' to quit.\n")


def main() -> None:
    assistant = Jarvis()
    print_banner()
    try:
        while True:
            try:
                raw = input("● You  ").strip()
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit.")
                continue
            response = assistant.handle(raw)
            if not response.text:
                continue
            if response.text == "__CLEAR__":
                clear_screen()
                print_banner()
                continue
            print(f"\n🤖 JARVIS\n{response.text}\n")
            if response.should_exit:
                break
    finally:
        assistant.memory.close()


if __name__ == "__main__":
    main()
