"""Zagonska točka aplikacije."""
from .common import *
from .constants import ERROR_LOG_FILE
from .helpers import log_startup_error
from .app import MatriculaApp


def main():
    sys.excepthook = log_startup_error
    root = None
    try:
        root = tk.Tk()
        MatriculaApp(root)
        root.mainloop()
    except Exception as exc:
        error_msg = traceback.format_exc()
        try:
            with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
                f.write(error_msg)
        except Exception:
            pass
        try:
            if root is None:
                root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Kritična napaka", f"Program se je sesul:\n{exc}")
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
