"""
Main entry point for the Renode UI application.

This script parses command-line arguments, sets up the Qt application and
event loop, initializes the RenodeBridge and MainWindow, and starts the
application.
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
    The main function of the application.

    Parses arguments, initializes the application, and starts the event loop.
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
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    bridge = RenodeBridge(sys_bus_params=sys_bus_params)
    window = MainWindow(bridge)
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
