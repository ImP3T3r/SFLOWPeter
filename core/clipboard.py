import subprocess
import time
import sys

_saved_app: str | None = None
_saved_hwnd: int | None = None
is_mac = sys.platform == "darwin"

def save_frontmost_app():
    """Save the currently focused application before recording starts."""
    global _saved_app, _saved_hwnd
    if is_mac:
        try:
            result = subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to get name of first process whose frontmost is true'],
                capture_output=True, text=True, timeout=2,
            )
            name = result.stdout.strip()
            if name and name != "Howl":
                _saved_app = name
        except Exception:
            pass
    elif sys.platform == "win32":
        try:
            import ctypes
            _saved_hwnd = getattr(ctypes, "windll").user32.GetForegroundWindow()
        except Exception:
            pass

def paste_text(text: str):
    """Copy text to clipboard and paste into the previously active app."""
    global _saved_app, _saved_hwnd
    if is_mac:
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
    else:
        import pyperclip, ctypes
        from pynput.keyboard import Controller, Key
        pyperclip.copy(text)
        if _saved_hwnd:
            try:
                getattr(ctypes, "windll").user32.SetForegroundWindow(_saved_hwnd)
                time.sleep(0.05)
            except Exception:
                pass
        keyboard = Controller()
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        _saved_hwnd = None

def undo_and_paste_text(new_text: str):
    """Undo the previous paste (Ctrl+Z/Cmd+Z) and paste the new refined text."""
    global _saved_app, _saved_hwnd
    if is_mac:
        # Restore focus first
        if _saved_app:
            try:
                subprocess.run(
                    ["osascript", "-e", f'tell application "{_saved_app}" to activate'],
                    check=True, timeout=2,
                )
                time.sleep(0.12)
            except Exception:
                pass
        # Copy new text
        subprocess.run(["pbcopy"], input=new_text.encode("utf-8"), check=True)
        # Undo
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to keystroke "z" using command down'],
            check=True,
        )
        time.sleep(0.1)
        # Paste
        subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to keystroke "v" using command down'],
            check=True,
        )
        _saved_app = None
    else:
        import pyperclip, ctypes
        from pynput.keyboard import Controller, Key
        if _saved_hwnd:
            try:
                getattr(ctypes, "windll").user32.SetForegroundWindow(_saved_hwnd)
                time.sleep(0.05)
            except Exception:
                pass
        pyperclip.copy(new_text)
        keyboard = Controller()
        with keyboard.pressed(Key.ctrl):
            keyboard.press('z')
            keyboard.release('z')
        time.sleep(0.1)
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        _saved_hwnd = None
