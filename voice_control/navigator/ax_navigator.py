import os
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
