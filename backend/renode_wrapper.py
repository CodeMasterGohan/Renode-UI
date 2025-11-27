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
    """
    Wrapper for the Renode emulation environment.

    This class handles the initialization and control of the Renode emulator,
    managing the lifecycle of the emulation and providing methods to interact
    with it, such as loading scripts, starting/pausing/resetting simulation,
    and reading memory. It handles both real execution (if pyrenode3 is available)
    and mock execution for testing purposes.
    """

    def __init__(self, sys_bus_params=None):
        """
        Initializes the RenodeWrapper.

        Args:
            sys_bus_params (str, optional): Comma-separated key=value pairs for
                system bus parameters. Defaults to None.
        """
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

    def setup_logging(self, callback):
        """
        Sets up Renode logging to a temporary file and tails it.

        This method configures Renode to log to a temporary file and starts a
        background thread to read new lines from that file and pass them to
        the provided callback function.

        Args:
            callback (callable): A function that accepts a single string argument
                (the log message) and processes it.
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
        """
        Tails a log file and invokes a callback for each new line.

        This internal method runs in a separate thread. It continuously reads
        from the specified log file until the stop_event is set.

        Args:
            path (str): The path to the log file to tail.
            callback (callable): The function to call with each new log line.
            stop_event (threading.Event): An event to signal when to stop tailing.
        """
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
        """
        Cleans up resources used by the wrapper.

        Stops the logging thread and removes the temporary log file.
        """
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
        """
        Loads a Renode script into the emulator.

        Args:
            path (str): The file path to the Renode script (.resc).

        Raises:
            Exception: If loading the script fails in the Renode environment.
            ValueError: If the path is invalid (in Mock mode).
        """
        logger.info(f"Loading script: {path}")
        if PYRENODE_AVAILABLE:
            try:
                self.emulation.clear()
                self.monitor.execute(f"i @{path}")
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
        """
        Starts the Renode simulation.

        Raises:
            Exception: If starting the simulation fails.
        """
        logger.info("Starting simulation...")
        if PYRENODE_AVAILABLE:
            try:
                self.emulation.StartAll()
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
        """
        Pauses the Renode simulation.

        Raises:
            Exception: If pausing the simulation fails.
        """
        logger.info("Pausing simulation...")
        if PYRENODE_AVAILABLE:
            try:
                self.emulation.PauseAll()
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
        """
        Resets the Renode simulation.

        Clears the current emulation state.

        Raises:
            Exception: If resetting the simulation fails.
        """
        logger.info("Resetting simulation...")
        if PYRENODE_AVAILABLE:
            try:
                self.emulation.clear()
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
        """
        Reads a value from memory at the specified address.

        Args:
            addr (int): The memory address to read from.
            width (int): The width of the data to read in bytes (e.g., 4).

        Returns:
            int: The value read from memory. In Mock mode, returns a dummy value.
        """
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
