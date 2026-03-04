import subprocess
import time

_saved_app: str | None = None


def save_frontmost_app():
    """Save the currently focused application before recording starts."""
    global _saved_app
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of first process whose frontmost is true'],
            capture_output=True, text=True, timeout=2,
        )
        name = result.stdout.strip()
        if name and name != "SFlow":
            _saved_app = name
    except Exception:
        pass


def paste_text(text: str):
    """Copy text to clipboard and paste into the previously active app."""
    global _saved_app
    # Copy to clipboard
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)

    # Restore focus to the app that was active before recording
    if _saved_app:
        try:
            subprocess.run(
                ["osascript", "-e", f'tell application "{_saved_app}" to activate'],
                check=True, timeout=2,
            )
            time.sleep(0.12)
        except Exception:
            pass

    # Simulate Cmd+V
    subprocess.run(
        ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
        check=True,
    )
    _saved_app = None
