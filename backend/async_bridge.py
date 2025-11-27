import asyncio
from .renode_wrapper import RenodeWrapper

class RenodeBridge:
    """
    Asynchronous bridge for communicating with the RenodeWrapper.

    This class provides an async interface to the synchronous RenodeWrapper,
    allowing integration with async event loops (like QEventLoop/asyncio).
    It offloads blocking operations to a separate thread executor.
    """

    def __init__(self, sys_bus_params=None):
        """
        Initializes the RenodeBridge.

        Args:
            sys_bus_params (str, optional): Comma-separated key=value pairs for
                system bus parameters, passed to the wrapper. Defaults to None.
        """
        self.wrapper = RenodeWrapper(sys_bus_params=sys_bus_params)
        self.loop = asyncio.get_event_loop()

    async def load_script(self, path: str):
        """
        Asynchronously loads a Renode script.

        Args:
            path (str): The file path to the Renode script.
        """
        await self.loop.run_in_executor(None, self.wrapper.load_script, path)

    async def start(self):
        """
        Asynchronously starts the Renode simulation.
        """
        await self.loop.run_in_executor(None, self.wrapper.start)

    async def pause(self):
        """
        Asynchronously pauses the Renode simulation.
        """
        await self.loop.run_in_executor(None, self.wrapper.pause)

    async def reset(self):
        """
        Asynchronously resets the Renode simulation.
        """
        await self.loop.run_in_executor(None, self.wrapper.reset)

    async def read_memory(self, addr: int, width: int) -> int:
        """
        Asynchronously reads a value from memory.

        Args:
            addr (int): The memory address to read from.
            width (int): The width of the data to read in bytes.

        Returns:
            int: The value read from memory.
        """
        return await self.loop.run_in_executor(None, self.wrapper.read_memory, addr, width)

    def setup_logging(self, callback):
        """
        Sets up logging with a thread-safe callback.

        This method wraps the provided callback to ensure it is invoked on the
        main thread (or the event loop's thread) using `call_soon_threadsafe`.

        Args:
            callback (callable): A function to handle log messages.
        """
        def safe_callback(msg):
            self.loop.call_soon_threadsafe(callback, msg)
        
        # This doesn't need to be async as it just sets up the thread
        self.wrapper.setup_logging(safe_callback)
