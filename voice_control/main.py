from .utils.text import normalize_text
from .intent.extractor import extract_intent
from .executor.action_executor import execute


def on_speech_recognized(text: str):
    print(f"Raw STT: {text}")

    clean = normalize_text(text)
    print(f"Normalized: {clean}")

    intent, target = extract_intent(clean)
    print(f"Intent: {intent}, Target: {target}")

    if intent:
        result = execute(intent, target)
        if result is not None:
            print(result)
    else:
        print("No recognizable command")


if __name__ == "__main__":
    # Simple manual test
    on_speech_recognized("open gmail")
