"""
Generic handlers for all OSes.

Includes:
- FileHandler

"""

from pathlib import Path
from typing import Dict, Any
from .base import BaseFileHandler
import base64

def resolve_path(path: str) -> Path:
    """Resolve a path to its absolute path. Expand ~ to the user's home directory."""
    return Path(path).expanduser().resolve()

class GenericFileHandler(BaseFileHandler):
    async def file_exists(self, path: str) -> Dict[str, Any]:
        try:
            return {"success": True, "exists": resolve_path(path).is_file()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def directory_exists(self, path: str) -> Dict[str, Any]:
        try:
            return {"success": True, "exists": resolve_path(path).is_dir()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_dir(self, path: str) -> Dict[str, Any]:
        try:
            return {"success": True, "files": [p.name for p in resolve_path(path).iterdir() if p.is_file() or p.is_dir()]}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def read_text(self, path: str) -> Dict[str, Any]:
        try:
            return {"success": True, "content": resolve_path(path).read_text()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_text(self, path: str, content: str) -> Dict[str, Any]:
        try:
            resolve_path(path).write_text(content)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_bytes(self, path: str, content_b64: str) -> Dict[str, Any]:
        try:
            resolve_path(path).write_bytes(base64.b64decode(content_b64))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def read_bytes(self, path: str) -> Dict[str, Any]:
        try:
            return {"success": True, "content_b64": base64.b64encode(resolve_path(path).read_bytes()).decode('utf-8')}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_file(self, path: str) -> Dict[str, Any]:
        try:
            resolve_path(path).unlink()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_dir(self, path: str) -> Dict[str, Any]:
        try:
            resolve_path(path).mkdir(parents=True, exist_ok=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_dir(self, path: str) -> Dict[str, Any]:
        try:
            resolve_path(path).rmdir()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
