"""
Generic handlers for all OSes.

Includes:
- FileHandler

"""

from pathlib import Path
from typing import Dict, Any, Optional
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

    async def write_bytes(self, path: str, content_b64: str, append: bool = False) -> Dict[str, Any]:
        try:
            mode = 'ab' if append else 'wb'
            with open(resolve_path(path), mode) as f:
                f.write(base64.b64decode(content_b64))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def read_bytes(self, path: str, offset: int = 0, length: Optional[int] = None) -> Dict[str, Any]:
        try:
            file_path = resolve_path(path)
            with open(file_path, 'rb') as f:
                if offset > 0:
                    f.seek(offset)
                
                if length is not None:
                    content = f.read(length)
                else:
                    content = f.read()
                
            return {"success": True, "content_b64": base64.b64encode(content).decode('utf-8')}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_file_size(self, path: str) -> Dict[str, Any]:
        try:
            file_path = resolve_path(path)
            size = file_path.stat().st_size
            return {"success": True, "size": size}
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
