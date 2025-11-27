# Renode UI

A modern, responsive graphical user interface for the [Renode](https://renode.io/) simulation framework, built with Python and PySide6. This application allows users to control Renode simulations, inspect memory in real-time, and view logs in a user-friendly environment.

## Features

*   **Simulation Control**: Load scripts (`.resc`), start, pause, and reset simulations.
*   **Memory Monitoring**: Watch specific memory addresses with real-time updates. Supports various data types.
*   **Dual Log View**:
    *   **App Logs**: Internal application logs for debugging the UI.
    *   **Renode Monitor**: Real-time output from the Renode monitor.
*   **Asynchronous Architecture**: Built with `asyncio` and `qasync` to ensure a responsive UI even during heavy simulation operations.
*   **Mock Mode**: Automatically falls back to a mock backend if `pyrenode3` is not installed, allowing for UI development and testing without a full Renode setup.

## Project Structure

*   `main.py`: Entry point of the application.
*   `main_window.py`: Main UI implementation using PySide6.
*   `backend/`:
    *   `renode_wrapper.py`: Synchronous wrapper around `pyrenode3` (or mock backend).
    *   `async_bridge.py`: Asynchronous bridge connecting the UI to the wrapper.
*   `widgets/`: Custom UI widgets.
    *   `memory_watch.py`: Widget for managing memory watches.

## Prerequisites

*   **Python 3.10+**
*   **System Dependencies**:
    *   `mono-devel` (required for `pythonnet`/`pyrenode3` interaction with Renode on Linux)
    *   `libxcb-xinerama0`, `libxcb-cursor0` (required for Qt6 on Linux)
*   **Renode**: The Renode framework must be installed.

## Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd renode-ui
    ```

2.  **Run the Setup/Launch Script**:
    The provided `run_ui.sh` script handles virtual environment creation and dependency installation.
    ```bash
    ./run_ui.sh
    ```

    *Alternatively, manual setup:*
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python main.py
    ```

## Usage

### Starting the Application
Run the application using the helper script:
```bash
./run_ui.sh
```
Or directly via Python (if environment is active):
```bash
python main.py
```

### Controlling Simulation
1.  **Load Script**: Click "Load Script" to select a `.resc` file.
2.  **Start**: Click "Start" to begin execution.
3.  **Pause**: Click "Pause" to halt execution temporarily.
4.  **Reset**: Click "Reset" to clear the state and reload.

### Monitoring Memory
1.  Click "Add Watch" in the Memory Watch section.
2.  Enter the hex address (e.g., `0x80001000`), a name, and select the type.
3.  Values will update periodically while the simulation is running.

## Development

### Documentation
The codebase is fully documented with Google-style docstrings.

### Troubleshooting
*   **Mock Mode Warning**: If you see "RenodeWrapper initialized (Mock)" in the logs, it means `pyrenode3` was not found. The app will simulate behavior. To fix, ensure `pyrenode3` is installed and Mono is correctly configured.
*   **Freezes**: The app uses `qasync` to prevent freezing. If the UI locks up, check for blocking calls in the main thread.
