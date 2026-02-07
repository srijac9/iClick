from ..resolver.target_resolver import resolve_and_open
from ..navigator.ax_navigator import (
    run_accessibility_open,
    run_search,
    run_play,
    run_scroll,
    run_calendar_open,
    run_set_reminder,
)

def execute(intent: str, target: str):
    if intent == "open" and target:
        ax = run_accessibility_open(target)
        if ax:
            return ax
        return resolve_and_open(target)
    if intent == "search" and target:
        return run_search(target)
    if intent == "play" and target:
        return run_play(target)
    if intent == "scroll":
        return run_scroll(target)
    if intent == "calendar_open":
        return run_calendar_open()
    if intent == "reminder" and target:
        return run_set_reminder(target)

    return "No action taken"
