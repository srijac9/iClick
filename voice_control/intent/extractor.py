def extract_intent(text: str):
    """
    Extracts intent and target from speech.
    Example:
      'open gmail' -> ('open', 'gmail')
    """
    words = text.split()

    if not words:
        return None, None

    if words[0] in ("open", "launch", "start"):
        intent = "open"
        target = " ".join(words[1:])
        return intent, target

    return None, None
