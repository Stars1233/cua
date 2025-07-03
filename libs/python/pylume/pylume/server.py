import os
import time
import asyncio
import subprocess
import tempfile
import logging
import socket
from typing import Optional
import sys
from .exceptions import LumeConnectionError
import signal
import json
import shlex
import random
from logging import getLogger


class LumeServer:
    def __init__(
        self,
        debug: bool = False,
        server_start_timeout: int = 60,
        port: Optional[int] = None,
        use_existing_server: bool = False,
        host: str = "localhost",
    ):
        """Initialize the LumeServer.

        Args:
            debug: Enable debug logging
            server_start_timeout: Timeout in seconds to wait for server to start
            port: Specific port to use for the server
            use_existing_server: If True, will try to connect to an existing server
                               instead of starting a new one
            host: Host to use for connections (e.g., "localhost", "127.0.0.1", "host.docker.internal")
        """
        self.debug = debug
        self.server_start_timeout = server_start_timeout
        self.server_process = None
        self.output_file = None
        self.requested_port = port
        self.port = None
        self.base_url = None
        self.use_existing_server = use_existing_server
        self.host = host

        # Configure logging
        self.logger = getLogger("pylume.server")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG if debug else logging.INFO)

        self.logger.debug(f"Server initialized with host: {self.host}")

    def _check_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                result = s.connect_ex(("127.0.0.1", port))
                if result == 0:  # Port is in use on localhost
                    return False
        except:
            pass

        # Check the specified host (e.g., "host.docker.internal") if it's not a localhost alias
        if self.host not in ["localhost", "127.0.0.1"]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    result = s.connect_ex((self.host, port))
                    if result == 0:  # Port is in use on host
                        return False
            except:
                pass

        return True

    def _get_server_port(self) -> int:
        """Get an available port for the server."""
        # Use requested port if specified
        if self.requested_port is not None:
            if not self._check_port_available(self.requested_port):
                raise RuntimeError(f"Requested port {self.requested_port} is not available")
            return self.requested_port

        # Find a free port
        for _ in range(10):  # Try up to 10 times
            port = random.randint(49152, 65535)
            if self._check_port_available(port):
                return port

        raise RuntimeError("Could not find an available port")

    async def _ensure_server_running(self) -> None:
        """Ensure the lume server is running, start it if it's not."""
        try:
            self.logger.debug("Checking if lume server is running...")
            # Try to connect to the server with a short timeout
            cmd = ["curl", "-s", "-w", "%{http_code}", "-m", "5", f"{self.base_url}/vms"]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                response = stdout.decode()
                status_code = int(response[-3:])
                if status_code == 200:
                    self.logger.debug("PyLume server is running")
                    return

            self.logger.debug("PyLume server not running, attempting to start it")
            # Server not running, try to start it
            lume_path = os.path.join(os.path.dirname(__file__), "lume")
            if not os.path.exists(lume_path):
                raise RuntimeError(f"Could not find lume binary at {lume_path}")

            # Make sure the file is executable
            os.chmod(lume_path, 0o755)

            # Create a temporary file for server output
            self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
            self.logger.debug(f"Using temporary file for server output: {self.output_file.name}")

            # Start the server
            self.logger.debug(f"Starting lume server with: {lume_path} serve --port {self.port}")

            # Start server in background using subprocess.Popen
            try:
                self.server_process = subprocess.Popen(
                    [lume_path, "serve", "--port", str(self.port)],
                    stdout=self.output_file,
                    stderr=self.output_file,
                    cwd=os.path.dirname(lume_path),
                    start_new_session=True,  # Run in new session to avoid blocking
                )
            except Exception as e:
                self.output_file.close()
                os.unlink(self.output_file.name)
                raise RuntimeError(f"Failed to start lume server process: {str(e)}")

            # Wait for server to start
            self.logger.debug(
                f"Waiting up to {self.server_start_timeout} seconds for server to start..."
            )
            start_time = time.time()
            server_ready = False
            last_size = 0

            while time.time() - start_time < self.server_start_timeout:
                if self.server_process.poll() is not None:
                    # Process has terminated
                    self.output_file.seek(0)
                    output = self.output_file.read()
                    self.output_file.close()
                    os.unlink(self.output_file.name)
                    error_msg = (
                        f"Server process terminated unexpectedly.\n"
                        f"Exit code: {self.server_process.returncode}\n"
                        f"Output: {output}"
                    )
                    raise RuntimeError(error_msg)

                # Check output file for server ready message
                self.output_file.seek(0, os.SEEK_END)
                size = self.output_file.tell()
                if size > last_size:  # Only read if there's new content
                    self.output_file.seek(last_size)
                    new_output = self.output_file.read()
                    if new_output.strip():  # Only log non-empty output
                        self.logger.debug(f"Server output: {new_output.strip()}")
                    last_size = size

                    if "Server started" in new_output:
                        server_ready = True
                        self.logger.debug("Server startup detected")
                        break

                # Try to connect to the server periodically
                try:
                    cmd = ["curl", "-s", "-w", "%{http_code}", "-m", "5", f"{self.base_url}/vms"]
                    process = await asyncio.create_subprocess_exec(
                        *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()

                    if process.returncode == 0:
                        response = stdout.decode()
                        status_code = int(response[-3:])
                        if status_code == 200:
                            server_ready = True
                            self.logger.debug("Server is responding to requests")
                            break
                except:
                    pass  # Server not ready yet

                await asyncio.sleep(1.0)

            if not server_ready:
                # Cleanup if server didn't start
                if self.server_process:
                    self.server_process.terminate()
                    try:
                        self.server_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.server_process.kill()
                self.output_file.close()
                os.unlink(self.output_file.name)
                raise RuntimeError(
                    f"Failed to start lume server after {self.server_start_timeout} seconds. "
                    "Check the debug output for more details."
                )

            # Give the server a moment to fully initialize
            await asyncio.sleep(2.0)

            # Verify server is responding
            try:
                cmd = ["curl", "-s", "-w", "%{http_code}", "-m", "10", f"{self.base_url}/vms"]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise RuntimeError(f"Curl command failed: {stderr.decode()}")

                response = stdout.decode()
                status_code = int(response[-3:])

                if status_code != 200:
                    raise RuntimeError(f"Server returned status code {status_code}")

                self.logger.debug("PyLume server started successfully")
            except Exception as e:
                self.logger.debug(f"Server verification failed: {str(e)}")
                if self.server_process:
                    self.server_process.terminate()
                    try:
                        self.server_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.server_process.kill()
                self.output_file.close()
                os.unlink(self.output_file.name)
                raise RuntimeError(f"Server started but is not responding: {str(e)}")

            self.logger.debug("Server startup completed successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to start lume server: {str(e)}")

    async def _start_server(self) -> None:
        """Start the lume server using the lume executable."""
        self.logger.debug("Starting PyLume server")

        # Get absolute path to lume executable in the same directory as this file
        lume_path = os.path.join(os.path.dirname(__file__), "lume")
        if not os.path.exists(lume_path):
            raise RuntimeError(f"Could not find lume binary at {lume_path}")

        try:
            # Make executable
            os.chmod(lume_path, 0o755)

            # Get and validate port
            self.port = self._get_server_port()
            self.base_url = f"http://{self.host}:{self.port}/lume"

            # Set up output handling
            self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)

            # Start the server process with the lume executable
            env = os.environ.copy()
            env["RUST_BACKTRACE"] = "1"  # Enable backtrace for better error reporting

            # Specify the host to bind to (0.0.0.0 to allow external connections)
            self.server_process = subprocess.Popen(
                [lume_path, "serve", "--port", str(self.port)],
                stdout=self.output_file,
                stderr=subprocess.STDOUT,
                cwd=os.path.dirname(lume_path),  # Run from same directory as executable
                env=env,
            )

            # Wait for server to initialize
            await asyncio.sleep(2)
            await self._wait_for_server()

        except Exception as e:
            await self._cleanup()
            raise RuntimeError(f"Failed to start lume server process: {str(e)}")

    async def _tail_log(self) -> None:
        """Read and display server log output in debug mode."""
        while True:
            try:
                self.output_file.seek(0, os.SEEK_END)  # type: ignore[attr-defined]
                line = self.output_file.readline()  # type: ignore[attr-defined]
                if line:
                    line = line.strip()
                    if line:
                        print(f"SERVER: {line}")
                if self.server_process.poll() is not None:  # type: ignore[attr-defined]
                    print("Server process ended")
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error reading log: {e}")
                await asyncio.sleep(0.1)

    async def _wait_for_server(self) -> None:
        """Wait for server to start and become responsive with increased timeout."""
        start_time = time.time()
        while time.time() - start_time < self.server_start_timeout:
            if self.server_process.poll() is not None:  # type: ignore[attr-defined]
                error_msg = await self._get_error_output()
                await self._cleanup()
                raise RuntimeError(error_msg)

            try:
                await self._verify_server()
                self.logger.debug("Server is now responsive")
                return
            except Exception as e:
                self.logger.debug(f"Server not ready yet: {str(e)}")
                await asyncio.sleep(1.0)

        await self._cleanup()
        raise RuntimeError(f"Server failed to start after {self.server_start_timeout} seconds")

    async def _verify_server(self) -> None:
        """Verify server is responding to requests."""
        try:
            cmd = [
                "curl",
                "-s",
                "-w",
                "%{http_code}",
                "-m",
                "10",
                f"http://{self.host}:{self.port}/lume/vms",
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"Curl command failed: {stderr.decode()}")

            response = stdout.decode()
            status_code = int(response[-3:])

            if status_code != 200:
                raise RuntimeError(f"Server returned status code {status_code}")

            self.logger.debug("PyLume server started successfully")
        except Exception as e:
            raise RuntimeError(f"Server not responding: {str(e)}")

    async def _get_error_output(self) -> str:
        """Get error output from the server process."""
        if not self.output_file:
            return "No output available"
        self.output_file.seek(0)
        output = self.output_file.read()
        return (
            f"Server process terminated unexpectedly.\n"
            f"Exit code: {self.server_process.returncode}\n"  # type: ignore[attr-defined]
            f"Output: {output}"
        )

    async def _cleanup(self) -> None:
        """Clean up all server resources."""
        if self.server_process:
            try:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
            except:
                pass
            self.server_process = None

        # Clean up output file
        if self.output_file:
            try:
                self.output_file.close()
                os.unlink(self.output_file.name)
            except Exception as e:
                self.logger.debug(f"Error cleaning up output file: {e}")
            self.output_file = None

    async def ensure_running(self) -> None:
        """Ensure the server is running.

        If use_existing_server is True, will only try to connect to an existing server.
        Otherwise will:
          1. Try to connect to an existing server on the specified port
          2. If that fails and not in Docker, start a new server
          3. If in Docker and no existing server is found, raise an error
        """
        # First check if we're in Docker
        in_docker = os.path.exists("/.dockerenv") or (
            os.path.exists("/proc/1/cgroup") and "docker" in open("/proc/1/cgroup", "r").read()
        )

        # If using a non-localhost host like host.docker.internal, set up the connection details
        if self.host not in ["localhost", "127.0.0.1"]:
            if self.requested_port is None:
                raise RuntimeError("Port must be specified when using a remote host")

            self.port = self.requested_port
            self.base_url = f"http://{self.host}:{self.port}/lume"
            self.logger.debug(f"Using remote host server at {self.base_url}")

            # Try to verify the server is accessible
            try:
                await self._verify_server()
                self.logger.debug("Successfully connected to remote server")
                return
            except Exception as e:
                if self.use_existing_server or in_docker:
                    # If explicitly requesting an existing server or in Docker, we can't start a new one
                    raise RuntimeError(
                        f"Failed to connect to remote server at {self.base_url}: {str(e)}"
                    )
                else:
                    self.logger.debug(f"Remote server not available at {self.base_url}: {str(e)}")
                    # Fall back to localhost for starting a new server
                    self.host = "localhost"

        # If explicitly using an existing server, verify it's running
        if self.use_existing_server:
            if self.requested_port is None:
                raise RuntimeError("Port must be specified when using an existing server")

            self.port = self.requested_port
            self.base_url = f"http://{self.host}:{self.port}/lume"

            try:
                await self._verify_server()
                self.logger.debug("Successfully connected to existing server")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to connect to existing server at {self.base_url}: {str(e)}"
                )
        else:
            # Try to connect to an existing server first
            if self.requested_port is not None:
                self.port = self.requested_port
                self.base_url = f"http://{self.host}:{self.port}/lume"

                try:
                    await self._verify_server()
                    self.logger.debug("Successfully connected to existing server")
                    return
                except Exception:
                    self.logger.debug(f"No existing server found at {self.base_url}")

                    # If in Docker and can't connect to existing server, raise an error
                    if in_docker:
                        raise RuntimeError(
                            f"Failed to connect to server at {self.base_url} and cannot start a new server in Docker"
                        )

            # Start a new server
            self.logger.debug("Starting a new server instance")
            await self._start_server()

    async def stop(self) -> None:
        """Stop the server if we're managing it."""
        if not self.use_existing_server:
            self.logger.debug("Stopping lume server...")
            await self._cleanup()
