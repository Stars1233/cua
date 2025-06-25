"""
File System Interface Tests
Tests for the file system methods of the Computer interface (macOS).
Required environment variables:
- CUA_API_KEY: API key for C/ua cloud provider
- CUA_CONTAINER_NAME: Name of the container to use
"""

import os
import asyncio
import pytest
from pathlib import Path
import sys
import traceback

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
print(f"Loading environment from: {env_file}")
from dotenv import load_dotenv

load_dotenv(env_file)

# Add paths to sys.path if needed
pythonpath = os.environ.get("PYTHONPATH", "")
for path in pythonpath.split(":"):
    if path and path not in sys.path:
        sys.path.insert(0, path)  # Insert at beginning to prioritize
        print(f"Added to sys.path: {path}")

from computer import Computer, VMProviderType

@pytest.fixture(scope="session")
async def computer():
    """Shared Computer instance for all test cases."""
    # Create a remote Linux computer with C/ua
    computer = Computer(
        os_type="linux",
        api_key=os.getenv("CUA_API_KEY"),
        name=str(os.getenv("CUA_CONTAINER_NAME")),
        provider_type=VMProviderType.CLOUD,
    )
    
    # Create a local macOS computer with C/ua
    # computer = Computer()
    
    # Connect to host computer
    # computer = Computer(use_host_computer_server=True)
    
    try:
        await computer.run()
        yield computer
    finally:
        await computer.disconnect()

@pytest.mark.asyncio(loop_scope="session")
async def test_file_exists(computer):
    tmp_path = "test_file_exists.txt"
    # Ensure file does not exist
    if await computer.interface.file_exists(tmp_path):
        await computer.interface.delete_file(tmp_path)
    exists = await computer.interface.file_exists(tmp_path)
    assert exists is False, f"File {tmp_path} should not exist"
    # Create file and check again
    await computer.interface.write_text(tmp_path, "hello")
    exists = await computer.interface.file_exists(tmp_path)
    assert exists is True, f"File {tmp_path} should exist"
    await computer.interface.delete_file(tmp_path)


@pytest.mark.asyncio(loop_scope="session")
async def test_directory_exists(computer):
    tmp_dir = "test_directory_exists"
    if await computer.interface.directory_exists(tmp_dir):
        # Remove all files in directory before removing directory
        files = await computer.interface.list_dir(tmp_dir)
        for fname in files:
            await computer.interface.delete_file(f"{tmp_dir}/{fname}")
        # Remove the directory itself
        await computer.interface.delete_dir(tmp_dir)
    exists = await computer.interface.directory_exists(tmp_dir)
    assert exists is False, f"Directory {tmp_dir} should not exist"
    await computer.interface.create_dir(tmp_dir)
    exists = await computer.interface.directory_exists(tmp_dir)
    assert exists is True, f"Directory {tmp_dir} should exist"
    # Cleanup: remove files and directory
    files = await computer.interface.list_dir(tmp_dir)
    for fname in files:
        await computer.interface.delete_file(f"{tmp_dir}/{fname}")
    await computer.interface.delete_dir(tmp_dir)


@pytest.mark.asyncio(loop_scope="session")
async def test_list_dir(computer):
    tmp_dir = "test_list_dir"
    if not await computer.interface.directory_exists(tmp_dir):
        await computer.interface.create_dir(tmp_dir)
    files = ["foo.txt", "bar.txt"]
    for fname in files:
        await computer.interface.write_text(f"{tmp_dir}/{fname}", "hi")
    result = await computer.interface.list_dir(tmp_dir)
    assert set(result) >= set(files), f"Directory {tmp_dir} should contain files {files}"
    for fname in files:
        await computer.interface.delete_file(f"{tmp_dir}/{fname}")
    await computer.interface.delete_dir(tmp_dir)


@pytest.mark.asyncio(loop_scope="session")
async def test_read_write_text(computer):
    tmp_path = "test_rw_text.txt"
    content = "sample text"
    await computer.interface.write_text(tmp_path, content)
    read = await computer.interface.read_text(tmp_path)
    assert read == content, "File content should match"
    await computer.interface.delete_file(tmp_path)


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_file(computer):
    tmp_path = "test_delete_file.txt"
    await computer.interface.write_text(tmp_path, "bye")
    exists = await computer.interface.file_exists(tmp_path)
    assert exists is True, "File should exist"
    await computer.interface.delete_file(tmp_path)
    exists = await computer.interface.file_exists(tmp_path)
    assert exists is False, "File should not exist"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_dir(computer):
    tmp_dir = "test_create_dir"
    if await computer.interface.directory_exists(tmp_dir):
        await computer.interface.delete_dir(tmp_dir)
    await computer.interface.create_dir(tmp_dir)
    exists = await computer.interface.directory_exists(tmp_dir)
    assert exists is True, "Directory should exist"
    await computer.interface.delete_dir(tmp_dir)

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
