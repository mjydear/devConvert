"""Desktop entry point used by the packaged Windows executable."""

import threading
import time
import webbrowser

import uvicorn

from app import app


URL = "http://127.0.0.1:8765"


def open_browser() -> None:
    time.sleep(1.2)
    webbrowser.open(URL)


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8765, reload=False, log_level="warning")
