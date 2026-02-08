import os
import re
import time
import subprocess

import pyautogui

try:
    from Quartz import (
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementSetAttributeValue,
        AXUIElementPerformAction,
        kAXWindowsAttribute,
        kAXFocusedAttribute,
        kAXChildrenAttribute,
        kAXTitleAttribute,
        kAXRoleAttribute,
        kAXRoleDescriptionAttribute,
        kAXPressAction,
    )
    _HAS_AX = True
except Exception:
    _HAS_AX = False


def _run_osascript(script: str):
    try:
        subprocess.run(["osascript", "-e", script], check=False)
        return True
    except Exception:
        return False


def _keystroke(key: str, modifiers=None):
    modifiers = modifiers or []
    if modifiers:
        mod = " using " + " ".join(f"{m} down" for m in modifiers)
    else:
        mod = ""
    script = f'tell application "System Events" to keystroke "{key}"{mod}'
    return _run_osascript(script)


def _key_code(code: int, modifiers=None):
    modifiers = modifiers or []
    if modifiers:
        mod = " using " + " ".join(f"{m} down" for m in modifiers)
    else:
        mod = ""
    script = f"tell application \"System Events\" to key code {code}{mod}"
    return _run_osascript(script)


def _get_output_volume():
    try:
        out = subprocess.check_output(["osascript", "-e", "output volume of (get volume settings)"])
        return int(out.decode().strip())
    except Exception:
        return None


def _set_output_volume(value: int):
    value = max(0, min(100, int(value)))
    return _run_osascript(f"set volume output volume {value}")


def _set_output_mute(muted: bool):
    flag = "true" if muted else "false"
    return _run_osascript(f"set volume output muted {flag}")


def _parse_volume_value(value: str):
    if not value:
        return None
    m = re.search(r"\d+", value)
    if not m:
        return None
    v = int(m.group())
    return max(0, min(100, v))


def _open_chrome():
    return _run_osascript('tell application "Google Chrome" to activate')

def _new_tab():
    return _run_osascript(
        'tell application "System Events" to keystroke "t" using command down'
    )


def _chrome_pid():
    try:
        out = subprocess.check_output(
            ["osascript", "-e", 'tell application "System Events" to get the unix id of process "Google Chrome"']
        )
        return int(out.decode().strip())
    except Exception:
        return None


def _walk_ax(element):
    try:
        children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute)
    except Exception:
        children = None
    if not children:
        return
    for child in children:
        yield child
        yield from _walk_ax(child)


def _focus_address_bar():
    # Try AX first for a true accessibility-driven focus.
    if _HAS_AX:
        pid = _chrome_pid()
        if pid:
            app = AXUIElementCreateApplication(pid)
            try:
                windows = AXUIElementCopyAttributeValue(app, kAXWindowsAttribute) or []
            except Exception:
                windows = []
            for win in windows:
                for el in _walk_ax(win):
                    try:
                        role = AXUIElementCopyAttributeValue(el, kAXRoleAttribute)
                        title = AXUIElementCopyAttributeValue(el, kAXTitleAttribute)
                        role_desc = AXUIElementCopyAttributeValue(el, kAXRoleDescriptionAttribute)
                    except Exception:
                        continue
                    if role == "AXTextField" and (
                        (title and "address" in str(title).lower())
                        or (role_desc and "address" in str(role_desc).lower())
                    ):
                        try:
                            AXUIElementSetAttributeValue(el, kAXFocusedAttribute, True)
                            AXUIElementPerformAction(el, kAXPressAction)
                            _move_to_address_bar_fallback()
                            return True
                        except Exception:
                            pass
    # Fallback: use keyboard shortcut to focus address bar.
    _move_to_address_bar_fallback()
    return _run_osascript(
        'tell application "System Events" to keystroke "l" using command down'
    )


def _type_and_enter(text: str):
    escaped = text.replace('"', '\\"')
    return _run_osascript(
        f'tell application "System Events" to keystroke "{escaped}"\n'
        'tell application "System Events" to key code 36'
    )


def _chrome_window_bounds():
    script = (
        'tell application "Google Chrome"\n'
        "  set b to bounds of front window\n"
        "end tell\n"
        "return b\n"
    )
    try:
        out = subprocess.check_output(["osascript", "-e", script])
        # Output like: 0, 23, 1440, 900
        parts = [p.strip() for p in out.decode().split(",")]
        if len(parts) != 4:
            return None
        return tuple(int(p) for p in parts)
    except Exception:
        return None


def _move_to_address_bar_fallback():
    # Move cursor to a likely address bar location for visible motion.
    b = _chrome_window_bounds()
    if not b:
        return False
    x1, y1, x2, y2 = b
    # Heuristic: address bar roughly near top-left, a bit inset.
    x = x1 + 200
    y = y1 + 55
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click()
    return True


def _click_first_google_result():
    # Move cursor to first result and click for visible cursor motion.
    coords = _get_first_result_center()
    if coords:
        x, y = coords
        pyautogui.moveTo(x, y, duration=0.35)
        pyautogui.click()
        return True
    # Fallback: JS click if we couldn't compute screen coords.
    return _run_osascript(_js_click_first_result())


def _js_click_first_result():
    js = (
        "var h=document.querySelector('a h3');"
        "if(h && h.parentElement){h.parentElement.click(); true;} else {false;}"
    )
    return (
        'tell application "Google Chrome"\n'
        "  tell active tab of front window\n"
        f'    execute javascript "{js}"\n'
        "  end tell\n"
        "end tell"
    )


def _get_first_result_center():
    # Compute screen coordinates for the first search result via JS.
    js = (
        "var h=document.querySelector('a h3');"
        "if(!h||!h.parentElement){'';} else {"
        "var r=h.getBoundingClientRect();"
        "var cx=r.left + r.width/2;"
        "var cy=r.top + r.height/2;"
        "var chromeX=window.screenX + (window.outerWidth - window.innerWidth)/2;"
        "var chromeY=window.screenY + (window.outerHeight - window.innerHeight);"
        "Math.round(chromeX+cx)+','+Math.round(chromeY+cy);"
        "}"
    )
    script = (
        'tell application "Google Chrome"\n'
        "  tell active tab of front window\n"
        f'    execute javascript "{js}"\n'
        "  end tell\n"
        "end tell"
    )
    try:
        out = subprocess.check_output(["osascript", "-e", script])
        s = out.decode().strip()
        if not s:
            return None
        parts = s.split(",")
        if len(parts) != 2:
            return None
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def _open_gmail_flow():
    _open_chrome()
    time.sleep(1.2)
    _new_tab()
    time.sleep(0.2)
    _focus_address_bar()
    time.sleep(0.1)
    _type_and_enter("gmail")
    time.sleep(2.0)
    _click_first_google_result()
    return "Opened Gmail via accessibility navigation"


def run_accessibility_open(target: str):
    target = (target or "").strip().lower()
    if not target:
        return None
    if target in {"gmail", "google mail", "googlemail"}:
        return _open_gmail_flow()
    # Generic flow: open Chrome, search target, click first result.
    _open_chrome()
    time.sleep(1.0)
    _new_tab()
    time.sleep(0.2)
    _focus_address_bar()
    time.sleep(0.1)
    _type_and_enter(target)
    time.sleep(2.0)
    _click_first_google_result()
    return f"Opened {target} via accessibility navigation"


def run_search(query: str):
    _open_chrome()
    time.sleep(1.0)
    _new_tab()
    time.sleep(0.2)
    _focus_address_bar()
    time.sleep(0.1)
    _type_and_enter(query)
    time.sleep(2.0)
    _click_first_google_result()
    return f"Searched and opened top result for: {query}"


def run_play(song: str):
    # Play by searching YouTube for the song and opening the first result.
    query = f"{song} youtube"
    _open_chrome()
    time.sleep(1.0)
    _new_tab()
    time.sleep(0.2)
    _focus_address_bar()
    time.sleep(0.1)
    _type_and_enter(query)
    time.sleep(2.0)
    _click_first_google_result()
    return f"Playing: {song}"


def run_scroll(direction: str):
    direction = (direction or "").lower()
    amount = -600 if direction in ("down", "lower") else 600
    pyautogui.scroll(amount)
    return f"Scrolled {direction or 'down'}"


def run_page_scroll(direction: str):
    direction = (direction or "").lower()
    amount = -1500 if direction == "down" else 1500
    pyautogui.scroll(amount)
    return f"Page scrolled {direction or 'down'}"


def run_scroll_top():
    # Large scroll up to approximate top.
    pyautogui.scroll(4000)
    return "Scrolled to top"


def run_scroll_bottom():
    pyautogui.scroll(-4000)
    return "Scrolled to bottom"


def run_volume_change(direction: str):
    direction = (direction or "").lower()
    current = _get_output_volume()
    if current is None:
        # Fallback: pick a reasonable target if we can't read current volume.
        target = 60 if direction == "up" else 40
        _set_output_volume(target)
        return f"Volume set to {target}"
    step = 10
    if direction == "up":
        target = min(100, current + step)
    elif direction == "down":
        target = max(0, current - step)
    else:
        target = current
    _set_output_volume(target)
    return f"Volume set to {target}"


def run_volume_set(value: str):
    parsed = _parse_volume_value(value)
    if parsed is None:
        return "No action taken"
    _set_output_volume(parsed)
    return f"Volume set to {parsed}"


def run_mute(muted: bool):
    _set_output_mute(muted)
    return "Muted" if muted else "Unmuted"


def run_calendar_open():
    _run_osascript('tell application "Calendar" to activate')
    return "Opened Calendar"


def run_calendar_add(text: str):
    title = text.strip() if text else ""
    if not title:
        title = "Meeting"
    escaped = title.replace('"', '\\"')
    script = (
        'tell application "Calendar"\n'
        "  activate\n"
        "  set startDate to (current date) + 300\n"
        "  set endDate to startDate + 3600\n"
        "  tell calendar 1 to make new event with properties {summary:\"%s\", start date:startDate, end date:endDate}\n"
        "end tell"
    ) % escaped
    _run_osascript(script)
    return f"Scheduled meeting: {title}"


def run_set_reminder(text: str):
    # Create a reminder in the Reminders app (more appropriate than Calendar for reminders).
    escaped = text.replace('"', '\\"')
    script = (
        'tell application "Reminders"\n'
        "  activate\n"
        f'  tell list \"Reminders\" to make new reminder with properties {{name:\"{escaped}\"}}\n'
        "end tell"
    )
    _run_osascript(script)
    return f"Set reminder: {text}"


def run_sleep():
    _run_osascript('tell application "System Events" to sleep')
    return "Sleeping"


def run_lock_screen():
    _run_osascript('tell application "System Events" to keystroke "q" using {command down, control down}')
    return "Locked screen"


def run_minimize_window():
    _keystroke("m", ["command"])
    return "Minimized window"


def run_fullscreen():
    _keystroke("f", ["control", "command"])
    return "Toggled fullscreen"


def run_back():
    _keystroke("[", ["command"])
    return "Back"


def run_forward():
    _keystroke("]", ["command"])
    return "Forward"


def run_select_all():
    _keystroke("a", ["command"])
    return "Selected all"


def run_copy():
    _keystroke("c", ["command"])
    return "Copied"


def run_paste():
    _keystroke("v", ["command"])
    return "Pasted"


def run_cut():
    _keystroke("x", ["command"])
    return "Cut"


def run_undo():
    _keystroke("z", ["command"])
    return "Undo"


def run_redo():
    _keystroke("z", ["command", "shift"])
    return "Redo"


def run_delete():
    _key_code(51)
    return "Deleted"


def run_type_text(text: str):
    if not text:
        return "No action taken"
    escaped = text.replace('"', '\\"')
    _run_osascript(f'tell application "System Events" to keystroke "{escaped}"')
    return f"Typed: {text}"
