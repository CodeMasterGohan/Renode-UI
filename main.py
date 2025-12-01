"""
Main Application Entry Point.

This module initializes the PySide6 application, sets up the asyncio event loop
using `qasync`, and launches the main window. It also handles command-line arguments
for configuring the Renode system bus.
"""

import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from main_window import MainWindow
from backend.async_bridge import RenodeBridge
import argparse

def main():
    """
    The main entry point for the application.

    This function:
    1. Parses command-line arguments.
    2. Initializes the QApplication.
    3. Sets up the application stylesheet.
    4. Configures the asyncio event loop with qasync.
    5. Initializes the RenodeBridge and MainWindow.
    6. Starts the event loop.
    """
    parser = argparse.ArgumentParser(description="Pacer UI application")
    parser.add_argument("--sys-bus-params", type=str,
                        help="Comma-separated key=value pairs for system bus parameters (e.g., 'key1=value1,key2=value2')")
    args = parser.parse_args()

    sys_bus_params = {}
    if args.sys_bus_params:
        for param in args.sys_bus_params.split(','):
            if '=' in param:
                key, value = param.split('=', 1)
                sys_bus_params[key.strip()] = value.strip()
            else:
                print(f"Warning: Invalid system bus parameter format: {param}. Skipping.")


    app = QApplication(sys.argv)
    from styles import DARK_THEME_QSS
    app.setStyleSheet(DARK_THEME_QSS)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    bridge = RenodeBridge(sys_bus_params=sys_bus_params)
    window = MainWindow(bridge)
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
