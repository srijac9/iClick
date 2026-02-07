import re

def normalize_text(text: str) -> str:
    """
    Cleans up speech-to-text output for reliable parsing
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text
