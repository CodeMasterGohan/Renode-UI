"""
Async Bridge Module.

This module provides an asynchronous bridge to the synchronous `RenodeWrapper`.
It ensures that blocking Renode operations run in a separate thread (executor)
to avoid freezing the asyncio event loop (and consequently the UI).
"""

import asyncio
from .renode_wrapper import RenodeWrapper

class RenodeBridge:
    """
    Asynchronous bridge for interacting with the Renode simulation.

    This class wraps `RenodeWrapper` methods, executing them in a thread pool
    executor to integrate seamlessy with asyncio-based applications (like the UI).
    """

    def __init__(self, sys_bus_params=None):
        """
        Initializes the RenodeBridge.

        Args:
            sys_bus_params (str, optional): Comma-separated key=value pairs for
                SystemBus parameters. Passed to the underlying RenodeWrapper.
        """
        self.wrapper = RenodeWrapper(sys_bus_params=sys_bus_params)
        self.loop = asyncio.get_event_loop()

    async def load_script(self, path: str):
        """
        Asynchronously loads a Renode script.

        This method delegates to `RenodeWrapper.load_script` running in a separate thread.

        Args:
            path (str): The path to the script file.
        """
        await self.loop.run_in_executor(None, self.wrapper.load_script, path)

    async def start(self):
        """
        Asynchronously starts the simulation.

        This method delegates to `RenodeWrapper.start` running in a separate thread.
        """
        await self.loop.run_in_executor(None, self.wrapper.start)

    async def pause(self):
        """
        Asynchronously pauses the simulation.

        This method delegates to `RenodeWrapper.pause` running in a separate thread.
        """
        await self.loop.run_in_executor(None, self.wrapper.pause)

    async def reset(self):
        """
        Asynchronously resets the simulation.

        This method delegates to `RenodeWrapper.reset` running in a separate thread.
        """
        await self.loop.run_in_executor(None, self.wrapper.reset)

    async def read_memory(self, addr: int, width: int) -> int:
        """
        Asynchronously reads memory from the simulation.

        This method delegates to `RenodeWrapper.read_memory` running in a separate thread.

        Args:
            addr (int): The memory address to read from.
            width (int): The width of the data to read.

        Returns:
            int: The value read from memory.
        """
        return await self.loop.run_in_executor(None, self.wrapper.read_memory, addr, width)

    def setup_logging(self, callback):
        """
        Sets up logging with a thread-safe callback.

        Wraps the provided callback to ensure it is invoked on the main asyncio loop
        via `call_soon_threadsafe`.

        Args:
            callback (callable): The function to call with log messages.
        """
        def safe_callback(msg):
            self.loop.call_soon_threadsafe(callback, msg)
        
        # This doesn't need to be async as it just sets up the thread
        self.wrapper.setup_logging(safe_callback)

    async def monitor_command(self, command: str):
        """
        Asynchronously executes a monitor command.

        This method delegates to `RenodeWrapper.monitor_command` running in a separate thread.

        Args:
            command (str): The monitor command to execute.
        """
        await self.loop.run_in_executor(None, self.wrapper.monitor_command, command)
