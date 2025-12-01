# Renode UI

A modern, dark-themed GUI frontend for [Renode](https://renode.io/), a simulated embedded environment. This application allows users to load scripts, control simulation execution (start, pause, reset), watch memory addresses, and interact with the Renode monitor directly.

## Purpose

The primary goal of this project is to provide a user-friendly interface for Renode simulations. It abstracts the complexity of the command-line interface and provides visual tools for debugging and monitoring emulated systems. It allows for:
- Easy script loading.
- Real-time simulation control.
- Memory monitoring in a structured table.
- Direct interaction with the Renode Monitor via a built-in console.

## Setup

### Prerequisites

Ensure you have a Linux environment (tested on Ubuntu/Debian based systems).

You need to install the following system dependencies:

```bash
sudo apt-get update
sudo apt-get install -y mono-devel libxcb-xinerama0 libxcb-cursor0
```

*   `mono-devel`: Required for `pythonnet`, which `pyrenode3` uses to communicate with Renode (written in C#).
*   `libxcb-xinerama0`, `libxcb-cursor0`: Required for Qt6 (PySide6) to run properly on Linux.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Run the UI:**
    The project includes a helper script `run_ui.sh` that sets up a virtual environment, installs Python dependencies, and launches the application.

    ```bash
    ./run_ui.sh
    ```

    If you need to specify a particular Python interpreter (e.g., to avoid conflicts with `pyenv` or `conda`):
    ```bash
    ./run_ui.sh --python /usr/bin/python3
    ```

## Usage

Once the application is running:

1.  **Load a Script**: Click the **Load Script** button to open a file dialog and select a `.resc` (Renode Script) file.
2.  **Control Simulation**:
    *   **Start**: Begins or resumes the simulation.
    *   **Pause**: Pauses the currently running simulation.
    *   **Reset**: Clears the emulation state.
3.  **Renode Monitor**: Switch to the **Renode Monitor** tab to see output from the Renode backend. You can type commands in the input box at the bottom (e.g., `help`, `sysbus`) and click **Send**.
4.  **Memory Watch**:
    *   Click **Add Watch** to monitor a specific memory address.
    *   Enter the Address (in Hex, e.g., `0x80000000`), a Name, and the Data Type.
    *   The value will update periodically while the simulation is running.
5.  **App Logs**: The **App Logs** tab shows internal application logs for debugging UI or backend issues.

## Architecture

The application follows a layered architecture to separate the UI from the simulation logic and ensure responsiveness:

1.  **UI Layer (`MainWindow`, `MemoryWatchWidget`)**: Built with PySide6. It handles user input and visualization. It communicates with the backend via the `RenodeBridge`.
2.  **Bridge Layer (`RenodeBridge`)**: An asynchronous bridge that lives in `backend/async_bridge.py`. It uses `asyncio` to manage tasks and delegates heavy/blocking operations to the wrapper in a separate thread executor. This prevents the UI from freezing during Renode operations.
3.  **Wrapper Layer (`RenodeWrapper`)**: Located in `backend/renode_wrapper.py`. This is a synchronous class that directly interacts with the `pyrenode3` library. It manages the `Emulation` and `Monitor` objects. It also features a **Mock Mode** that activates if `pyrenode3` or the Renode package is missing, allowing for UI development without the full simulation backend.
4.  **Renode Backend**: The actual Renode simulation engine (running via Mono/.NET), controlled by `pyrenode3`.

## Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

**Documentation**: Please ensure all new code is fully documented using Google Style Python Docstrings.

## Troubleshooting

*   **`pythonnet` installation fails**: Ensure `mono-devel` is installed (`sudo apt install mono-devel`).
*   **Qt platform plugin "xcb" error**: You are likely missing XCB libraries. Install them via `sudo apt install libxcb-xinerama0 libxcb-cursor0`.
*   **Renode not found**: The application attempts to auto-detect the `renode-latest.pkg.tar.xz` package in the root directory. Ensure it is present or set the `PYRENODE_PKG` environment variable to its path.
