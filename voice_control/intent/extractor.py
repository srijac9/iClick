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

    if first in ("open", "launch", "start"):
        return "open", " ".join(words[1:]).strip()

    if first in ("search", "find", "lookup"):
        return "search", " ".join(words[1:]).strip()

    if first in ("play", "listen"):
        if len(words) >= 2 and words[1] == "song":
            return "play", " ".join(words[2:]).strip()
        return "play", " ".join(words[1:]).strip()

    if first == "scroll":
        direction = words[1] if len(words) > 1 else "down"
        return "scroll", direction

    if first == "open" and len(words) >= 2 and words[1] == "calendar":
        return "calendar_open", None

    if first == "set" and len(words) >= 2 and words[1] == "reminder":
        return "reminder", " ".join(words[2:]).strip()

    if first == "reminder":
        return "reminder", " ".join(words[1:]).strip()

    if first == "remind" and len(words) >= 2 and words[1] == "me":
        return "reminder", " ".join(words[2:]).strip()

    return None, None
