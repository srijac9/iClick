from ..resolver.target_resolver import resolve_and_open
from ..navigator.ax_navigator import run_accessibility_open

def execute(intent: str, target: str):
    if intent == "open" and target:
        ax = run_accessibility_open(target)
        if ax:
            return ax
        return resolve_and_open(target)

    return "No action taken"
