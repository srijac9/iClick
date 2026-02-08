def _strip_fillers(text: str):
    if not text:
        return text
    fillers = ("for ", "to ", "a ", "an ", "the ", "please ", "my ")
    lowered = text.lower()
    for f in fillers:
        if lowered.startswith(f):
            return text[len(f):].strip()
    return text.strip()


def extract_intent(text: str):
    """
    Extracts intent and target from speech.
    Examples:
      'open gmail' -> ('open', 'gmail')
      'search coffee shops' -> ('search', 'coffee shops')
      'play song bohemian rhapsody' -> ('play', 'bohemian rhapsody')
      'scroll down' -> ('scroll', 'down')
      'open calendar' -> ('calendar_open', None)
      'set reminder buy milk' -> ('reminder', 'buy milk')
    """
    if not text:
        return None, None
    raw = text.strip()
    raw_words = raw.split()
    words = raw.lower().split()
    if not words:
        return None, None

    first = words[0]
    second = words[1] if len(words) > 1 else ""
    third = words[2] if len(words) > 2 else ""

    if first == "open" and len(words) >= 2:
        if second == "calendar":
            return "calendar_open", None
        if second in ("the", "a", "an") and third == "calendar":
            return "calendar_open", None

    if first in ("open", "launch", "start"):
        return "open", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first in ("close", "quit", "exit"):
        return "close", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first in ("switch", "focus"):
        return "switch", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first in ("maximize", "minimize", "fullscreen"):
        return first, None

    if first in ("back", "forward"):
        return first, None

    if first in ("go", "visit", "browse"):
        if second == "to":
            return "navigate", _strip_fillers(" ".join(raw_words[2:]).strip())
        return "navigate", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first == "open" and second in ("website", "site", "web"):
        return "navigate", _strip_fillers(" ".join(raw_words[2:]).strip())

    if first in ("search", "find", "lookup", "google"):
        if second == "for":
            return "search", _strip_fillers(" ".join(raw_words[2:]).strip())
        return "search", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first in ("play", "listen"):
        if len(words) >= 2 and second == "song":
            return "play", _strip_fillers(" ".join(raw_words[2:]).strip())
        return "play", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first in ("pause", "resume"):
        return first, None

    if first == "stop":
        return "pause", None

    if first in ("next", "previous", "prev"):
        return "media_next" if first == "next" else "media_prev", None

    if first == "mute":
        return "mute", None

    if first == "unmute":
        return "unmute", None

    if first == "volume":
        if second in ("up", "down"):
            return "volume", second
        if second in ("set", "to") and third:
            return "volume_set", _strip_fillers(" ".join(raw_words[2:]).strip())
        if second.isdigit():
            return "volume_set", second
        return "volume", None

    if first in ("turn", "raise", "lower", "increase", "decrease"):
        if "volume" in words:
            idx = words.index("volume")
            after = words[idx + 1] if idx + 1 < len(words) else ""
            if after in ("up", "down"):
                return "volume", after
            if first in ("increase", "raise"):
                return "volume", "up"
            if first in ("decrease", "lower"):
                return "volume", "down"
            if after == "on":
                return "unmute", None
            if after == "off":
                return "mute", None

    if first == "scroll":
        direction = second if second else "down"
        return "scroll", direction

    if first == "page" and second in ("up", "down"):
        return "page_scroll", second

    if first == "top":
        return "scroll_top", None

    if first == "bottom":
        return "scroll_bottom", None

    if first == "left" or first == "right":
        return "scroll", first

    if first in ("type", "dictate"):
        return "type", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first == "delete":
        return "delete", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first in ("undo", "redo"):
        return first, None

    if first == "select" and second in ("all", "everything"):
        return "select_all", None

    if first in ("copy", "paste", "cut"):
        return first, None

    if first == "set" and len(words) >= 2:
        if second in ("a", "an") and len(words) >= 3 and third == "reminder":
            return "reminder", _strip_fillers(" ".join(raw_words[3:]).strip())
        if second == "reminder":
            return "reminder", _strip_fillers(" ".join(raw_words[2:]).strip())

    if first == "reminder":
        return "reminder", _strip_fillers(" ".join(raw_words[1:]).strip())

    if first == "remind" and len(words) >= 2 and second == "me":
        return "reminder", _strip_fillers(" ".join(raw_words[2:]).strip())

    if first == "add" and second in ("event", "meeting"):
        return "calendar_add", _strip_fillers(" ".join(raw_words[2:]).strip())

    if first == "schedule":
        if second in ("meeting", "event"):
            return "calendar_add", _strip_fillers(" ".join(raw_words[2:]).strip())
        if second in ("a", "an", "the") and third in ("meeting", "event"):
            return "calendar_add", _strip_fillers(" ".join(raw_words[3:]).strip())

    if first == "calendar":
        return "calendar_open", None

    if first == "screenshot" or (first == "take" and second == "screenshot"):
        return "screenshot", None

    if first == "lock":
        if second == "screen":
            return "lock_screen", None
        if second in ("the", "my") and third == "screen":
            return "lock_screen", None

    if first in ("sleep", "shutdown", "restart"):
        return first, None

    if first == "run" and second in ("shortcut", "workflow"):
        return "shortcut", _strip_fillers(" ".join(raw_words[2:]).strip())

    if first in ("trigger", "execute"):
        return "shortcut", _strip_fillers(" ".join(raw_words[1:]).strip())

    return None, None
