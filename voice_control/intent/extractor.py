def _strip_fillers(text: str):
    if not text:
        return text
    fillers = ("for ", "to ", "a ", "an ", "the ")
    lowered = text
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
    words = text.split()
    if not words:
        return None, None

    first = words[0]

    if first == "open" and len(words) >= 2 and words[1] == "calendar":
        return "calendar_open", None

    if first in ("open", "launch", "start"):
        return "open", _strip_fillers(" ".join(words[1:]).strip())

    if first in ("search", "find", "lookup"):
        return "search", _strip_fillers(" ".join(words[1:]).strip())

    if first in ("play", "listen"):
        if len(words) >= 2 and words[1] == "song":
            return "play", _strip_fillers(" ".join(words[2:]).strip())
        return "play", _strip_fillers(" ".join(words[1:]).strip())

    if first == "scroll":
        direction = words[1] if len(words) > 1 else "down"
        return "scroll", direction

    if first == "set" and len(words) >= 2:
        if words[1] in ("a", "an") and len(words) >= 3 and words[2] == "reminder":
            return "reminder", _strip_fillers(" ".join(words[3:]).strip())
        if words[1] == "reminder":
            return "reminder", _strip_fillers(" ".join(words[2:]).strip())

    if first == "reminder":
        return "reminder", _strip_fillers(" ".join(words[1:]).strip())

    if first == "remind" and len(words) >= 2 and words[1] == "me":
        return "reminder", _strip_fillers(" ".join(words[2:]).strip())

    return None, None
