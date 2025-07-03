from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import uvicorn
import logging
import asyncio
import json
import traceback
import inspect
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from .handlers.factory import HandlerFactory
import os
import aiohttp

# Set up logging with more detail
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configure WebSocket with larger message size
WEBSOCKET_MAX_SIZE = 1024 * 1024 * 10  # 10MB limit

# Configure application with WebSocket settings
app = FastAPI(
    title="Computer API",
    description="API for the Computer project",
    version="0.1.0",
    websocket_max_size=WEBSOCKET_MAX_SIZE,
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Create OS-specific handlers
        self.accessibility_handler, self.automation_handler, self.diorama_handler, self.file_handler = HandlerFactory.create_handlers()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


manager = ConnectionManager()


@app.websocket("/ws", name="websocket_endpoint")
async def websocket_endpoint(websocket: WebSocket):
    # WebSocket message size is configured at the app or endpoint level, not on the instance
    await manager.connect(websocket)
    
    # Check if CONTAINER_NAME is set (indicating cloud provider)
    container_name = os.environ.get("CONTAINER_NAME")
    
    # If cloud provider, perform authentication handshake
    if container_name:
        try:
            logger.info(f"Cloud provider detected. CONTAINER_NAME: {container_name}. Waiting for authentication...")
            
            # Wait for authentication message
            auth_data = await websocket.receive_json()
            
            # Validate auth message format
            if auth_data.get("command") != "authenticate":
                await websocket.send_json({
                    "success": False,
                    "error": "First message must be authentication"
                })
                await websocket.close()
                manager.disconnect(websocket)
                return
            
            # Extract credentials
            client_api_key = auth_data.get("params", {}).get("api_key")
            client_container_name = auth_data.get("params", {}).get("container_name")
            
            # Layer 1: VM Identity Verification
            if client_container_name != container_name:
                logger.warning(f"VM name mismatch. Expected: {container_name}, Got: {client_container_name}")
                await websocket.send_json({
                    "success": False,
                    "error": "VM name mismatch"
                })
                await websocket.close()
                manager.disconnect(websocket)
                return
            
            # Layer 2: API Key Validation with TryCUA API
            if not client_api_key:
                await websocket.send_json({
                    "success": False,
                    "error": "API key required"
                })
                await websocket.close()
                manager.disconnect(websocket)
                return
            
            # Validate with TryCUA API
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {client_api_key}"
                    }
                    
                    async with session.get(
                        f"https://www.trycua.com/api/vm/auth?container_name={container_name}",
                        headers=headers,
                    ) as resp:
                        if resp.status != 200:
                            error_msg = await resp.text()
                            logger.warning(f"API validation failed: {error_msg}")
                            await websocket.send_json({
                                "success": False,
                                "error": "Authentication failed"
                            })
                            await websocket.close()
                            manager.disconnect(websocket)
                            return
                        
                        # If we get a 200 response with VNC URL, the VM exists and user has access
                        vnc_url = (await resp.text()).strip()
                        if not vnc_url:
                            logger.warning(f"No VNC URL returned for VM: {container_name}")
                            await websocket.send_json({
                                "success": False,
                                "error": "VM not found"
                            })
                            await websocket.close()
                            manager.disconnect(websocket)
                            return
                        
                        logger.info(f"Authentication successful for VM: {container_name}")
                        await websocket.send_json({
                            "success": True,
                            "message": "Authenticated"
                        })
            
            except Exception as e:
                logger.error(f"Error validating with TryCUA API: {e}")
                await websocket.send_json({
                    "success": False,
                    "error": "Authentication service unavailable"
                })
                await websocket.close()
                manager.disconnect(websocket)
                return

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await websocket.send_json({
                "success": False,
                "error": "Authentication failed"
            })
            await websocket.close()
            manager.disconnect(websocket)
            return

    # Map commands to appropriate handler methods
    handlers = {
        # App-Use commands
        "diorama_cmd": manager.diorama_handler.diorama_cmd,
        # Accessibility commands
        "get_accessibility_tree": manager.accessibility_handler.get_accessibility_tree,
        "find_element": manager.accessibility_handler.find_element,
        # Shell commands
        "run_command": manager.automation_handler.run_command,
        # File system commands
        "file_exists": manager.file_handler.file_exists,
        "directory_exists": manager.file_handler.directory_exists,
        "list_dir": manager.file_handler.list_dir,
        "read_text": manager.file_handler.read_text,
        "write_text": manager.file_handler.write_text,
        "read_bytes": manager.file_handler.read_bytes,
        "write_bytes": manager.file_handler.write_bytes,
        "get_file_size": manager.file_handler.get_file_size,
        "delete_file": manager.file_handler.delete_file,
        "create_dir": manager.file_handler.create_dir,
        "delete_dir": manager.file_handler.delete_dir,
        # Mouse commands
        "mouse_down": manager.automation_handler.mouse_down,
        "mouse_up": manager.automation_handler.mouse_up,
        "left_click": manager.automation_handler.left_click,
        "right_click": manager.automation_handler.right_click,
        "double_click": manager.automation_handler.double_click,
        "move_cursor": manager.automation_handler.move_cursor,
        "drag_to": manager.automation_handler.drag_to,
        "drag": manager.automation_handler.drag,
        # Keyboard commands
        "key_down": manager.automation_handler.key_down,
        "key_up": manager.automation_handler.key_up,
        "type_text": manager.automation_handler.type_text,
        "press_key": manager.automation_handler.press_key,
        "hotkey": manager.automation_handler.hotkey,
        # Scrolling actions
        "scroll": manager.automation_handler.scroll,
        "scroll_down": manager.automation_handler.scroll_down,
        "scroll_up": manager.automation_handler.scroll_up,
        # Screen actions
        "screenshot": manager.automation_handler.screenshot,
        "get_cursor_position": manager.automation_handler.get_cursor_position,
        "get_screen_size": manager.automation_handler.get_screen_size,
        # Clipboard actions
        "copy_to_clipboard": manager.automation_handler.copy_to_clipboard,
        "set_clipboard": manager.automation_handler.set_clipboard,
    }

    try:
        while True:
            try:
                data = await websocket.receive_json()
                command = data.get("command")
                params = data.get("params", {})

                if command not in handlers:
                    await websocket.send_json(
                        {"success": False, "error": f"Unknown command: {command}"}
                    )
                    continue

                try:
                    # Filter params to only include those accepted by the handler function
                    handler_func = handlers[command]
                    sig = inspect.signature(handler_func)
                    filtered_params = {k: v for k, v in params.items() if k in sig.parameters}
                    
                    result = await handler_func(**filtered_params)
                    await websocket.send_json({"success": True, **result})
                except Exception as cmd_error:
                    logger.error(f"Error executing command {command}: {str(cmd_error)}")
                    logger.error(traceback.format_exc())
                    await websocket.send_json({"success": False, "error": str(cmd_error)})

            except WebSocketDisconnect:
                raise
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON decode error: {str(json_err)}")
                await websocket.send_json(
                    {"success": False, "error": f"Invalid JSON: {str(json_err)}"}
                )
            except Exception as loop_error:
                logger.error(f"Error in message loop: {str(loop_error)}")
                logger.error(traceback.format_exc())
                await websocket.send_json({"success": False, "error": str(loop_error)})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Fatal error in websocket connection: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            await websocket.close()
        except:
            pass
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
