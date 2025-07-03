import asyncio

class DioramaComputer:
    """
    A minimal Computer-like interface for Diorama, compatible with ComputerAgent.
    Implements _initialized, run(), and __aenter__ for agent compatibility.
    """
    def __init__(self, diorama):
        self.diorama = diorama
        self.interface = self.diorama.interface
        self._initialized = False

    async def __aenter__(self):
        # Ensure the event loop is running (for compatibility)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        self._initialized = True
        return self

    async def run(self):
        # This is a stub for compatibility
        if not self._initialized:
            await self.__aenter__()
        return self
