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
FINAL_PREFIXES = ("🗣️ ", "🗣️")
WAKE_WORD = "hey buddy"
DEBUG = os.getenv("RUN_FROM_STT_DEBUG", "0") == "1"
DEBOUNCE_SECONDS = 2.0
SILENCE_TRIGGER_SECONDS = 2.0
WAKE_ARM_SECONDS = 20.0


def _extract_phrase(line: str):
    line = line.strip()
    if not line:
        return None
    for p in PREFIXES:
        if line.startswith(p):
            return line[len(p):].strip()
    lowered = line.lower()
    if any(k in lowered for k in ("buddy", "hey", "open", "search", "play", "scroll", "remind", "reminder")):
        return line
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
    # Return text after the last wake token (buddy or hey buddy).
    if "buddy" in cleaned:
        return cleaned.split("buddy")[-1].strip()
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


def _find_command(cleaned: str):
    # Find last command keyword and return (intent, target).
    parts = cleaned.split()
    if not parts:
        return None, None
    last_idx = -1
    last_cmd = None
    for i, w in enumerate(parts):
        if w in ("open", "search", "find", "lookup", "play", "scroll", "set", "remind", "stop"):
            last_idx = i
            last_cmd = w
    if last_idx == -1:
        return None, None
    target = " ".join(parts[last_idx + 1:]).strip()
    if last_cmd in ("search", "find", "lookup"):
        if target.startswith("for "):
            target = target[len("for "):].strip()
        return "search", target
    if last_cmd == "play":
        if target.startswith("song "):
            target = target[len("song "):].strip()
        return "play", target
    if last_cmd == "scroll":
        return "scroll", target or "down"
    if last_cmd == "set":
        if target.startswith("a reminder "):
            return "reminder", target[len("a reminder "):].strip()
        if target.startswith("an reminder "):
            return "reminder", target[len("an reminder "):].strip()
        if target.startswith("reminder "):
            return "reminder", target[len("reminder "):].strip()
    if last_cmd == "remind":
        if target.startswith("me"):
            return "reminder", target[len("me"):].strip()
        return "reminder", target
    if last_cmd == "open":
        return "open", target
    if last_cmd == "stop":
        return "stop", ""
    return None, None


def main():
    print("run_from_stt: ready", flush=True)
    last_command = None
    last_time = 0.0
    last_update = 0.0
    session_text = ""
    last_cleaned = ""
    last_with_wake = ""
    last_command_text = ""
    last_action_text = ""
    wake_armed_until = 0.0
    blocked_text = ""
    blocked_active = False
    try:
        sel = selectors.DefaultSelector()
        sel.register(sys.stdin, selectors.EVENT_READ)
        buffer = ""
        while True:
            events = sel.select(timeout=0.1)
            now = time.time()
            if events:
                chunk = sys.stdin.buffer.readline()
                if not chunk:
                    # EOF: process any pending buffered line, then trigger.
                    if buffer.strip():
                        phrase = _extract_phrase(buffer)
                        if phrase:
                            cleaned = _clean_phrase(phrase)
                            if cleaned:
                                session_text = cleaned
                                last_cleaned = cleaned
                                last_command_text = cleaned
                                intent_tmp, _ = _find_command(cleaned)
                                if intent_tmp and intent_tmp != "stop":
                                    last_action_text = cleaned
                                if "buddy" in cleaned or ("hey" in cleaned and "buddy" in cleaned):
                                    last_with_wake = cleaned
                    if not session_text:
                        session_text = last_with_wake or last_cleaned
                    if session_text:
                        if not (blocked_active and session_text == blocked_text):
                            triggered, last_command, last_time = _trigger_if_ready(
                            session_text,
                            last_command,
                            last_time,
                            now,
                            wake_armed_until,
                            last_command_text,
                            last_action_text,
                            )
                            if triggered:
                                blocked_active = True
                                blocked_text = session_text
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
                    if DEBUG:
                        print(f"run_from_stt: raw line -> {line.strip()}", flush=True)
                    phrase = _extract_phrase(line)
                    if phrase:
                        cleaned = _clean_phrase(phrase)
                        if cleaned:
                            if blocked_active and cleaned != blocked_text:
                                blocked_active = False
                            if DEBUG:
                                print(f"run_from_stt: cleaned -> {cleaned}", flush=True)
                            # STT final lines are cumulative; keep the latest only.
                            session_text = cleaned
                            last_update = now
                            last_cleaned = cleaned
                            last_command_text = cleaned
                            intent_tmp, _ = _find_command(cleaned)
                            if intent_tmp and intent_tmp != "stop":
                                last_action_text = cleaned
                            if "buddy" in cleaned or ("hey" in cleaned and "buddy" in cleaned):
                                wake_armed_until = now + WAKE_ARM_SECONDS
                                last_with_wake = cleaned
                            # If this is a final line, trigger immediately (no EOF required).
                            if line.strip().startswith(FINAL_PREFIXES):
                                if DEBUG:
                                    print(f"run_from_stt: final line -> {cleaned}", flush=True)
                                if not (blocked_active and session_text == blocked_text):
                                    triggered, last_command, last_time = _trigger_if_ready(
                                        session_text,
                                        last_command,
                                        last_time,
                                        now,
                                        wake_armed_until,
                                        last_command_text,
                                        last_action_text,
                                    )
                                    if triggered:
                                        blocked_active = True
                                        blocked_text = session_text
                                        session_text = ""
                                        print("run_from_stt: triggered on final", flush=True)
            # Trigger on silence after last update (for continuous streams).
            if session_text and (now - last_update) >= SILENCE_TRIGGER_SECONDS:
                if DEBUG:
                    print(
                        f"run_from_stt: silence trigger -> {session_text}",
                        flush=True,
                    )
                if not (blocked_active and session_text == blocked_text):
                    triggered, last_command, last_time = _trigger_if_ready(
                        session_text,
                        last_command,
                        last_time,
                        now,
                        wake_armed_until,
                        last_command_text,
                        last_action_text,
                    )
                    if triggered:
                        blocked_active = True
                        blocked_text = session_text
                        print("run_from_stt: triggered on silence", flush=True)
                        # Prevent repeated triggers without new speech.
                        session_text = ""
            # No action while streaming. Action triggers on EOF after auto-stop.
    except KeyboardInterrupt:
        pass


def _trigger_if_ready(
    session_text,
    last_command,
    last_time,
    now,
    wake_armed_until,
    last_command_text,
    last_action_text,
):
    # Require wake word or recent wake-armed window.
    if now > wake_armed_until:
        if "buddy" not in session_text and WAKE_WORD not in session_text and not ("hey" in session_text and "buddy" in session_text):
            return False, last_command, last_time
    cleaned = _extract_command(session_text) or session_text
    intent, target = _find_command(cleaned)
    if not intent:
        return False, last_command, last_time
    if intent == "stop":
        # Execute last non-stop command (if any), then stop.
        if last_action_text:
            cleaned_last = _extract_command(last_action_text) or last_action_text
            intent2, target2 = _find_command(cleaned_last)
            if intent2 and intent2 != "stop":
                command2 = f"{intent2} {target2}".strip()
                print(f"\nCMD: {command2}")
                on_speech_recognized(command2)
        print("\nCMD: stop")
        raise SystemExit(0)
    command = f"{intent} {target}".strip()
    now = time.time()
    if command != last_command or (now - last_time) > DEBOUNCE_SECONDS:
        print(f"\nCMD: {command}")
        on_speech_recognized(command)
        return True, command, now
    return False, last_command, last_time


if __name__ == "__main__":
    main()
