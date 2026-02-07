import sys
import os
import time
import selectors

# Ensure repo root is on sys.path when running as a script.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voice_control.main import on_speech_recognized


PREFIXES = ("📝 ", "📝", "🗣️ ", "🗣️")
WAKE_WORD = "hey buddy"
DEBOUNCE_SECONDS = 2.0
SILENCE_TRIGGER_SECONDS = 2.0


def _extract_phrase(line: str):
    line = line.strip()
    if not line:
        return None
    for p in PREFIXES:
        if line.startswith(p):
            return line[len(p):].strip()
    return None


def _clean_phrase(text: str):
    # Keep only a-z and spaces so STT artifacts don't break parsing.
    cleaned = []
    last_space = False
    for ch in text.lower():
        if "a" <= ch <= "z":
            cleaned.append(ch)
            last_space = False
        elif ch.isspace():
            if not last_space:
                cleaned.append(" ")
                last_space = True
    return "".join(cleaned).strip()


def _extract_command(cleaned: str):
    # Only trigger after the wake word appears. Be tolerant to split tokens.
    if WAKE_WORD in cleaned:
        return cleaned.split(WAKE_WORD)[-1].strip()
    parts = cleaned.split()
    try:
        hey_idx = parts.index("hey")
    except ValueError:
        return None
    buddy_idx = -1
    for i in range(hey_idx + 1, len(parts)):
        if parts[i] == "buddy":
            buddy_idx = i
            break
    if buddy_idx == -1:
        return None
    return " ".join(parts[buddy_idx + 1:]).strip()


def _find_open_target(cleaned: str):
    # Try to find the last "open <target>" sequence in the line.
    parts = cleaned.split()
    last_open_idx = -1
    for i, w in enumerate(parts):
        if w == "open":
            last_open_idx = i
    if last_open_idx == -1:
        return None
    target = " ".join(parts[last_open_idx + 1:]).strip()
    return target if target else None


def main():
    last_command = None
    last_time = 0.0
    last_update = 0.0
    session_text = ""
    try:
        sel = selectors.DefaultSelector()
        sel.register(sys.stdin, selectors.EVENT_READ)
        buffer = ""
        while True:
            events = sel.select(timeout=0.1)
            now = time.time()
            if events:
                chunk = sys.stdin.buffer.read(1024)
                if not chunk:
                    # EOF: process any pending buffered line, then trigger.
                    if buffer.strip():
                        phrase = _extract_phrase(buffer)
                        if phrase:
                            cleaned = _clean_phrase(phrase)
                            if cleaned:
                                session_text = cleaned
                    if session_text:
                        _trigger_if_ready(session_text, last_command, last_time)
                    break
                try:
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                except BrokenPipeError:
                    return
                text = chunk.decode("utf-8", errors="ignore")
                buffer += text.replace("\r", "\n")
                lines = buffer.split("\n")
                buffer = lines.pop()
                for line in lines:
                    phrase = _extract_phrase(line)
                    if phrase:
                        cleaned = _clean_phrase(phrase)
                        if cleaned:
                            # STT final lines are cumulative; keep the latest only.
                            session_text = cleaned
                            last_update = now
            # If we've had silence, trigger from the accumulated session text.
            if session_text and last_update and (now - last_update) >= SILENCE_TRIGGER_SECONDS:
                triggered, last_command, last_time = _trigger_if_ready(
                    session_text, last_command, last_time
                )
                session_text = ""
    except KeyboardInterrupt:
        pass


def _trigger_if_ready(session_text, last_command, last_time):
    cleaned = _extract_command(session_text)
    if not cleaned:
        return False, last_command, last_time
    target = _find_open_target(cleaned)
    if not target:
        return False, last_command, last_time
    command = f"open {target}"
    now = time.time()
    if command != last_command or (now - last_time) > DEBOUNCE_SECONDS:
        on_speech_recognized(command)
        return True, command, now
    return False, last_command, last_time


if __name__ == "__main__":
    main()
