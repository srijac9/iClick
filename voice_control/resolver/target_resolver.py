import subprocess
import webbrowser
import urllib.parse
import os

def find_mac_app(app_name: str):
    """
    Attempts to find a macOS application by name.
    Returns full app name if found, otherwise None.
    """
    app_name = app_name.lower()

    search_paths = [
        "/Applications",
        os.path.expanduser("~/Applications"),
        "/System/Applications"
    ]

    for path in search_paths:
        if not os.path.exists(path):
            continue

        for item in os.listdir(path):
            if item.lower().endswith(".app"):
                clean_name = item.lower().replace(".app", "")
                if app_name in clean_name:
                    return item

    return None


def open_mac_app(app_bundle_name: str):
    try:
        subprocess.Popen(["open", "-a", app_bundle_name])
        return True
    except Exception:
        return False


def open_web_app(target: str):
    """
    Opens the most likely official website via search.
    """
    query = f"{target} official website"
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)


def resolve_and_open(target: str):
    # 1️⃣ Try macOS app
    app = find_mac_app(target)
    if app:
        if open_mac_app(app):
            return f"Opened macOS app: {app}"

    # 2️⃣ Web fallback
    open_web_app(target)
    return f"Opened web search for: {target}"

