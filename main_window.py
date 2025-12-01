"""
Main Window Module.

This module defines the main application window for the Renode UI.
It orchestrates the UI components, handles user interactions, and manages
the communication with the Renode backend via the bridge.
"""

import asyncio
import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QTextEdit, QTabWidget, QLineEdit
from PySide6.QtGui import QFont

from widgets.memory_watch import MemoryWatchWidget

class LogHandler(logging.Handler, QObject):
    """
    Custom logging handler that emits a signal for each log record.

    This allows log messages to be displayed in the UI (QTextEdit) in a thread-safe manner.
    """
    log_signal = Signal(str)

    def __init__(self):
        """
        Initializes the LogHandler.
        """
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        """
        Emits the log record as a signal.

        Args:
            record (logging.LogRecord): The log record to emit.
        """
        msg = self.format(record)
        self.log_signal.emit(msg)

class MainWindow(QMainWindow):
    """
    The main window of the Renode UI application.

    This class sets up the user interface, including buttons for controlling the simulation,
    a memory watch widget, and tabs for logs and the Renode monitor. It also handles
    asynchronous operations for communicating with the Renode backend.
    """

    def __init__(self, bridge):
        """
        Initializes the MainWindow.

        Args:
            bridge (RenodeBridge): The bridge instance for communicating with Renode.
        """
        super().__init__()
        self.bridge = bridge
        self.setWindowTitle("Renode UI")
        self.resize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Status Label
        self.status_label = QLabel("Status: Stopped")
        self.layout.addWidget(self.status_label)

        # Controls Layout
        controls_layout = QHBoxLayout()
        self.layout.addLayout(controls_layout)

        # Buttons
        self.load_btn = QPushButton("Load Script")
        self.load_btn.clicked.connect(self.load_script_handler)
        controls_layout.addWidget(self.load_btn)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(lambda: asyncio.ensure_future(self.start_simulation()))
        controls_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(lambda: asyncio.ensure_future(self.pause_simulation()))
        self.pause_btn.setEnabled(False)
        controls_layout.addWidget(self.pause_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(lambda: asyncio.ensure_future(self.reset_simulation()))
        controls_layout.addWidget(self.reset_btn)

        # Memory Watch Widget
        self.memory_watch = MemoryWatchWidget()
        self.layout.addWidget(self.memory_watch)

        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tab 1: App Logs
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.tabs.addTab(self.log_view, "App Logs")

        # Tab 2: Renode Monitor
        monitor_widget = QWidget()
        monitor_layout = QVBoxLayout(monitor_widget)
        
        self.renode_monitor = QTextEdit()
        self.renode_monitor.setReadOnly(True)
        # self.renode_monitor.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
        self.renode_monitor.setFont(QFont("Monospace"))
        monitor_layout.addWidget(self.renode_monitor)
        
        # Monitor Input Controls
        input_layout = QHBoxLayout()
        self.monitor_input = QLineEdit()
        self.monitor_input.setPlaceholderText("Enter monitor command...")
        self.monitor_input.returnPressed.connect(self.send_monitor_command)
        input_layout.addWidget(self.monitor_input)
        
        self.monitor_send_btn = QPushButton("Send")
        self.monitor_send_btn.clicked.connect(self.send_monitor_command)
        input_layout.addWidget(self.monitor_send_btn)
        
        monitor_layout.addLayout(input_layout)
        
        self.tabs.addTab(monitor_widget, "Renode Monitor")

        # Setup Logging
        self.log_handler = LogHandler()
        self.log_handler.log_signal.connect(self.log_view.append)
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

        # Setup Renode Logging
        self.bridge.setup_logging(self.append_renode_log)

        # Monitoring Task
        self.monitor_task = None

    def append_renode_log(self, msg):
        """
        Appends a log message to the Renode monitor view.

        Args:
            msg (str): The message to append.
        """
        self.renode_monitor.append(msg)
        # Auto scroll
        sb = self.renode_monitor.verticalScrollBar()
        sb.setValue(sb.maximum())

        # Monitoring Task
        self.monitor_task = None

    def load_script_handler(self):
        """
        Opens a file dialog to select a Renode script and initiates loading.
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Renode Script", "", "Renode Scripts (*.resc);;All Files (*)")
        if file_name:
            asyncio.ensure_future(self.load_script(file_name))

    async def load_script(self, path):
        """
        Asynchronously loads a Renode script.

        Args:
            path (str): The path to the script file.
        """
        try:
            await self.bridge.load_script(path)
            self.status_label.setText(f"Status: Loaded {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    async def start_simulation(self):
        """
        Asynchronously starts the simulation.
        """
        try:
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.status_label.setText("Status: Running")
            await self.bridge.start()
            
            if not self.monitor_task or self.monitor_task.done():
                self.monitor_task = asyncio.create_task(self.monitor_loop())
        except Exception as e:
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.status_label.setText("Status: Error")
            QMessageBox.critical(self, "Error", str(e))

    async def pause_simulation(self):
        """
        Asynchronously pauses the simulation.
        """
        try:
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.status_label.setText("Status: Paused")
            await self.bridge.pause()
            # Monitor loop will check bridge status or we can cancel it.
            # For now, let it run but it might just read same values or we can stop it.
            # Better to let it run if we want to see state changes, but usually we stop polling if paused?
            # The roadmap says "Runs while simulation is running".
            if self.monitor_task:
                self.monitor_task.cancel()
        except Exception as e:
            self.status_label.setText("Status: Error")
            QMessageBox.critical(self, "Error", str(e))

    async def reset_simulation(self):
        """
        Asynchronously resets the simulation.
        """
        try:
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.status_label.setText("Status: Stopped")
            await self.bridge.reset()
            if self.monitor_task:
                self.monitor_task.cancel()
        except Exception as e:
            self.status_label.setText("Status: Error")
            QMessageBox.critical(self, "Error", str(e))

    async def monitor_loop(self):
        """
        Background task that periodically polls memory watches while the simulation is running.
        """
        try:
            while True:
                # In a real app, check if simulation is actually running
                # For now, we assume if this task is running, we should poll
                
                # Iterate over watches
                # We need to access watches safely. 
                # Since we are in the same thread (asyncio on main thread), it's safe to read self.memory_watch.watches
                for i, watch in enumerate(self.memory_watch.watches):
                    try:
                        val = await self.bridge.read_memory(watch['address'], 4) # Default to 4 bytes for now
                        self.memory_watch.update_value(watch['row'], val)
                    except Exception as e:
                        logging.error(f"Error reading memory: {e}")
                
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass

    def send_monitor_command(self):
        """
        Sends the user-entered monitor command to the backend.

        This method retrieves the command from the input field, clears the field,
        and schedules the command execution asynchronously.
        """
        cmd = self.monitor_input.text().strip()
        if not cmd:
            return
        
        self.monitor_input.clear()
        
        try:
            asyncio.ensure_future(self._send_monitor_command_async(cmd))
        except Exception as e:
             QMessageBox.critical(self, "Error", str(e))

    async def _send_monitor_command_async(self, cmd):
        """
        Helper method to execute the monitor command asynchronously.

        Args:
            cmd (str): The command to execute.
        """
        try:
            if asyncio.iscoroutinefunction(self.bridge.monitor_command):
                await self.bridge.monitor_command(cmd)
            else:
                self.bridge.monitor_command(cmd)
                
        except Exception as e:
             QMessageBox.critical(self, "Error", str(e))
