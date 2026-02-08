from ..resolver.target_resolver import resolve_and_open
from ..navigator.ax_navigator import (
    run_accessibility_open,
    run_search,
    run_play,
    run_scroll,
    run_page_scroll,
    run_scroll_top,
    run_scroll_bottom,
    run_calendar_open,
    run_calendar_add,
    run_set_reminder,
    run_volume_change,
    run_volume_set,
    run_mute,
    run_sleep,
    run_minimize_window,
    run_fullscreen,
    run_back,
    run_forward,
    run_select_all,
    run_copy,
    run_paste,
    run_cut,
    run_undo,
    run_redo,
    run_delete,
    run_type_text,
    run_lock_screen,
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
    if intent == "page_scroll":
        return run_page_scroll(target)
    if intent == "scroll_top":
        return run_scroll_top()
    if intent == "scroll_bottom":
        return run_scroll_bottom()
    if intent == "calendar_open":
        return run_calendar_open()
    if intent == "calendar_add":
        return run_calendar_add(target)
    if intent == "reminder" and target:
        return run_set_reminder(target)
    if intent == "volume":
        return run_volume_change(target)
    if intent == "volume_set":
        return run_volume_set(target)
    if intent == "mute":
        return run_mute(True)
    if intent == "unmute":
        return run_mute(False)
    if intent == "sleep":
        return run_sleep()
    if intent == "lock_screen":
        return run_lock_screen()
    if intent == "minimize":
        return run_minimize_window()
    if intent == "fullscreen":
        return run_fullscreen()
    if intent == "back":
        return run_back()
    if intent == "forward":
        return run_forward()
    if intent == "select_all":
        return run_select_all()
    if intent == "copy":
        return run_copy()
    if intent == "paste":
        return run_paste()
    if intent == "cut":
        return run_cut()
    if intent == "undo":
        return run_undo()
    if intent == "redo":
        return run_redo()
    if intent == "delete":
        return run_delete()
    if intent == "type":
        return run_type_text(target)

    return "No action taken"
