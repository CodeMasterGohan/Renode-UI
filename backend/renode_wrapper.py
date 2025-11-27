import time
import logging
import traceback
import os
import threading
import tempfile
import shutil

# Try to import pyrenode3
try:
    import pyrenode3
    from pyrenode3.wrappers import Emulation, Monitor
    PYRENODE_AVAILABLE = True
except (ImportError, RuntimeError):
    PYRENODE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RenodeWrapper:
    def __init__(self, sys_bus_params=None):
        self.running = False
        self.emulation = None
        self.monitor = None
        if PYRENODE_AVAILABLE:
            if sys_bus_params:
                self.emulation = Emulation(sysBusParams=sys_bus_params)
            else:
                self.emulation = Emulation()
            self.monitor = Monitor()
            logger.info("RenodeWrapper initialized (Real)")
        else:
            logger.warning("pyrenode3 not found. Falling back to Mock mode.")
            logger.info("RenodeWrapper initialized (Mock)")

        self.log_file_path = None
        self.log_thread = None
        self.stop_logging_event = None
        self.log_callback = None

    def _execute_and_log(self, command: str):
        """
        Executes a monitor command and logs the output/error via the callback.
        Returns (output, error).
        """
        if not PYRENODE_AVAILABLE:
            return "", ""
        
        try:
            # Echo command
            if self.log_callback:
                self.log_callback(f"(monitor) {command}")
            
            output, error = self.monitor.execute(command)
            
            if output and self.log_callback:
                self.log_callback(output.strip())
            
            if error and self.log_callback:
                self.log_callback(f"Error: {error.strip()}")
                
            return output, error
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Exception executing '{command}': {e}")
            raise e

    def setup_logging(self, callback):
        self.log_callback = callback
        """
        Sets up Renode logging to a temporary file and tails it, 
        calling `callback` with each new line.
        """
        if not PYRENODE_AVAILABLE:
            logger.warning("Logging not available in Mock mode")
            return

        # Create a temp file
        fd, self.log_file_path = tempfile.mkstemp(prefix="renode_log_", suffix=".txt")
        os.close(fd)
        # Ensure it's empty/exists
        with open(self.log_file_path, 'w') as f:
            pass

        logger.info(f"Renode logging to: {self.log_file_path}")

        # Tell Renode to log to this file
        try:
            self.monitor.execute(f"logFile @{self.log_file_path}")
            self.monitor.execute("logLevel 0") # Capture everything
        except Exception as e:
            logger.error(f"Failed to setup logFile: {e}")
            return

        # Start tailing thread
        self.stop_logging_event = threading.Event()
        self.log_thread = threading.Thread(
            target=self._tail_log_file, 
            args=(self.log_file_path, callback, self.stop_logging_event),
            daemon=True
        )
        self.log_thread.start()

    def _tail_log_file(self, path, callback, stop_event):
        logger.info("Log tailing started")
        try:
            with open(path, "r") as f:
                # Go to end? No, we want to see startup logs if any.
                # But if we just created it, it's empty.
                while not stop_event.is_set():
                    line = f.readline()
                    if line:
                        callback(line.strip())
                    else:
                        time.sleep(0.1)
        except Exception as e:
            logger.error(f"Log tailing error: {e}")
        finally:
            logger.info("Log tailing stopped")

    def cleanup(self):
        if self.stop_logging_event:
            self.stop_logging_event.set()
        if self.log_thread:
            self.log_thread.join(timeout=1.0)
        
        if self.log_file_path and os.path.exists(self.log_file_path):
            try:
                os.remove(self.log_file_path)
            except OSError:
                pass


    def load_script(self, path: str):
        logger.info(f"Loading script: {path}")
        if PYRENODE_AVAILABLE:
            try:
                self.emulation.clear()
                
                # Use execute_script to properly capture errors
                if self.log_callback:
                    self.log_callback(f"(monitor) i @{path}")
                
                output, error = self.monitor.execute_script(path)
                
                if output and self.log_callback:
                    self.log_callback(output.strip())
                
                if error:
                    if self.log_callback:
                        self.log_callback(f"Error: {error.strip()}")
                    raise Exception(f"Renode Error: {error}")
                    
                logger.info("Script loaded successfully")
            except Exception as e:
                logger.error("Failed to load script. Exception type: %s", type(e))
                logger.error("Exception details: %s", e)
                logger.error("Traceback: %s", traceback.format_exc())
                raise e
        else:
            time.sleep(0.5) # Simulate work
            if not path:
                raise ValueError("Invalid path")
            logger.info("Script loaded successfully")

    def start(self):
        logger.info("Starting simulation...")
        if PYRENODE_AVAILABLE:
            try:
                # self.emulation.StartAll()
                output, error = self._execute_and_log("start")
                if error:
                     raise Exception(f"Renode Error: {error}")
                self.running = True
                logger.info("Simulation started")
            except Exception as e:
                logger.error("Failed to start simulation. Exception type: %s", type(e))
                logger.error("Exception details: %s", e)
                logger.error("Traceback: %s", traceback.format_exc())
                raise e
        else:
            time.sleep(0.2)
            self.running = True
            logger.info("Simulation started")

    def pause(self):
        logger.info("Pausing simulation...")
        if PYRENODE_AVAILABLE:
            try:
                # self.emulation.PauseAll()
                output, error = self._execute_and_log("pause")
                if error:
                     raise Exception(f"Renode Error: {error}")
                self.running = False
                logger.info("Simulation paused")
            except Exception as e:
                logger.error(f"Failed to pause simulation: {e}")
                raise e
        else:
            time.sleep(0.1)
            self.running = False
            logger.info("Simulation paused")

    def reset(self):
        logger.info("Resetting simulation...")
        if PYRENODE_AVAILABLE:
            try:
                # self.emulation.clear()
                output, error = self._execute_and_log("Clear")
                if error:
                     raise Exception(f"Renode Error: {error}")
                self.running = False
                logger.info("Simulation reset")
            except Exception as e:
                logger.error(f"Failed to reset simulation: {e}")
                raise e
        else:
            time.sleep(0.5)
            self.running = False
            logger.info("Simulation reset")

    def read_memory(self, addr: int, width: int) -> int:
        if PYRENODE_AVAILABLE:
            # TODO: Implement real memory read using pyrenode3
            # For now, we'll just log and return a dummy value to avoid crashing
            # if we don't know the exact API.
            # Ideally: return Monitor.execute(f"sysbus ReadDoubleWord {addr}") (parsed)
            return 0xDEADBEEF
        else:
            # Simulate memory read
            # logger.debug(f"Reading memory at {hex(addr)}") # Commented out to avoid spam
            time.sleep(0.01) # fast read
            return 0xDEADBEEF # Mock value
