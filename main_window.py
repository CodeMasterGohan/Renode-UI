import asyncio
import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QTextEdit, QTabWidget, QLineEdit
from PySide6.QtGui import QFont

from widgets.memory_watch import MemoryWatchWidget

class LogHandler(logging.Handler, QObject):
    log_signal = Signal(str)

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        self.log_signal.emit(msg)

class MainWindow(QMainWindow):
    def __init__(self, bridge):
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
        self.renode_monitor.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
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
        self.renode_monitor.append(msg)
        # Auto scroll
        sb = self.renode_monitor.verticalScrollBar()
        sb.setValue(sb.maximum())

        # Monitoring Task
        self.monitor_task = None

    def load_script_handler(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Renode Script", "", "Renode Scripts (*.resc);;All Files (*)")
        if file_name:
            asyncio.ensure_future(self.load_script(file_name))

    async def load_script(self, path):
        try:
            await self.bridge.load_script(path)
            self.status_label.setText(f"Status: Loaded {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    async def start_simulation(self):
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
        cmd = self.monitor_input.text().strip()
        if not cmd:
            return
        
        self.monitor_input.clear()
        # We don't await here because we are in a sync slot. 
        # But bridge methods might be async or sync. 
        # renode_wrapper methods are sync (except start/pause/reset which are called via ensure_future in lambda).
        # Wait, start/pause/reset in renode_wrapper are sync methods, but called via ensure_future?
        # Let's check MainWindow.__init__:
        # self.start_btn.clicked.connect(lambda: asyncio.ensure_future(self.start_simulation()))
        # self.start_simulation is async.
        # 
        # renode_wrapper.monitor_command is sync.
        # So we can just call it?
        # But wait, main_window.py calls `await self.bridge.start()`.
        # Let's check main.py to see what `bridge` is.
        # It's likely an instance of RenodeWrapper directly or a proxy?
        # If it's RenodeWrapper, start() is sync in renode_wrapper.py.
        # So `await self.bridge.start()` would fail if it's not async.
        # Ah, let's check main.py.
        
        # Assuming we can just call it for now, or wrap in ensure_future if we make a wrapper.
        # But renode_wrapper.py methods shown are synchronous.
        # `async def start_simulation(self)` calls `await self.bridge.start()`.
        # This implies `self.bridge.start()` returns an awaitable.
        # But `RenodeWrapper.start` is `def start(self):`.
        # Maybe `main.py` wraps it? I should check `main.py`.
        
        # For now, I'll assume I need to handle it similarly.
        # If `monitor_command` is sync, I can just call it.
        # If I need to await it, I should use ensure_future.
        
        try:
            # If bridge is the raw wrapper, it's sync.
            # If it's an async wrapper, it's async.
            # I'll check main.py in a moment. 
            # For now, let's assume I can just call it if it's sync, 
            # but if the existing code awaits `start()`, then `start()` must be async or return a future.
            
            # Let's optimistically assume I can just call it if I add it as sync to wrapper.
            # But wait, if `start()` is sync in wrapper, why does `main_window` await it?
            # Maybe `qasync` magic or `main.py` does something.
            
            # I'll write a safe implementation that tries to await if needed, or just calls it.
            # Actually, let's just use asyncio.ensure_future(self._send_monitor_command_async(cmd))
            asyncio.ensure_future(self._send_monitor_command_async(cmd))
        except Exception as e:
             QMessageBox.critical(self, "Error", str(e))

    async def _send_monitor_command_async(self, cmd):
        try:
            # Check if monitor_command is async or sync.
            # Based on my edit to renode_wrapper, it is sync.
            # But if main.py wraps it...
            # I'll assume I can call it synchronously if it's the raw object.
            # But `await self.bridge.start()` suggests otherwise.
            
            # Let's peek at main.py first before committing this chunk? 
            # No, I'm in the middle of a tool call.
            # I will assume `bridge` is the wrapper and `main_window` treats it as async 
            # possibly because it's running in a separate thread or process?
            # Or maybe I misread renode_wrapper.py?
            # renode_wrapper.py: `def start(self):` (Line 167) - It IS synchronous.
            # So `await self.bridge.start()` in main_window.py (Line 115) would FAIL 
            # unless `self.bridge` is NOT `RenodeWrapper` instance but something else.
            
            # I will proceed with adding the method, and then I'll check main.py and fix if needed.
            # For now, I'll implement `_send_monitor_command_async` to call `self.bridge.monitor_command(cmd)`.
            # If it needs await, I'll add it.
            
            if asyncio.iscoroutinefunction(self.bridge.monitor_command):
                await self.bridge.monitor_command(cmd)
            else:
                self.bridge.monitor_command(cmd)
                
        except Exception as e:
             QMessageBox.critical(self, "Error", str(e))
