"""
Windows implementation of automation and accessibility handlers.

This implementation uses pyautogui for GUI automation and Windows-specific APIs
for accessibility and system operations.
"""
from typing import Dict, Any, List, Tuple, Optional
import logging
import subprocess
import base64
import os
from io import BytesIO

# Configure logger
logger = logging.getLogger(__name__)

# Try to import pyautogui
try:
    import pyautogui
    logger.info("pyautogui successfully imported, GUI automation available")
except Exception as e:
    logger.error(f"pyautogui import failed: {str(e)}. GUI operations will not work.")
    pyautogui = None

# Try to import Windows-specific modules
try:
    import win32gui
    import win32con
    import win32api
    logger.info("Windows API modules successfully imported")
    WINDOWS_API_AVAILABLE = True
except Exception as e:
    logger.error(f"Windows API modules import failed: {str(e)}. Some Windows-specific features will be unavailable.")
    WINDOWS_API_AVAILABLE = False

from .base import BaseAccessibilityHandler, BaseAutomationHandler

class WindowsAccessibilityHandler(BaseAccessibilityHandler):
    """Windows implementation of accessibility handler."""
    
    async def get_accessibility_tree(self) -> Dict[str, Any]:
        """Get the accessibility tree of the current window."""
        if not WINDOWS_API_AVAILABLE:
            return {"success": False, "error": "Windows API not available"}
        
        try:
            # Get the foreground window
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return {"success": False, "error": "No foreground window found"}
            
            # Get window information
            window_text = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            tree = {
                "role": "Window",
                "title": window_text,
                "position": {"x": rect[0], "y": rect[1]},
                "size": {"width": rect[2] - rect[0], "height": rect[3] - rect[1]},
                "children": []
            }
            
            # Enumerate child windows
            def enum_child_proc(hwnd_child, children_list):
                try:
                    child_text = win32gui.GetWindowText(hwnd_child)
                    child_rect = win32gui.GetWindowRect(hwnd_child)
                    child_class = win32gui.GetClassName(hwnd_child)
                    
                    child_info = {
                        "role": child_class,
                        "title": child_text,
                        "position": {"x": child_rect[0], "y": child_rect[1]},
                        "size": {"width": child_rect[2] - child_rect[0], "height": child_rect[3] - child_rect[1]},
                        "children": []
                    }
                    children_list.append(child_info)
                except Exception as e:
                    logger.debug(f"Error getting child window info: {e}")
                return True
            
            win32gui.EnumChildWindows(hwnd, enum_child_proc, tree["children"])
            
            return {"success": True, "tree": tree}
            
        except Exception as e:
            logger.error(f"Error getting accessibility tree: {e}")
            return {"success": False, "error": str(e)}
    
    async def find_element(self, role: Optional[str] = None,
                          title: Optional[str] = None,
                          value: Optional[str] = None) -> Dict[str, Any]:
        """Find an element in the accessibility tree by criteria."""
        if not WINDOWS_API_AVAILABLE:
            return {"success": False, "error": "Windows API not available"}
        
        try:
            # Find window by title if specified
            if title:
                hwnd = win32gui.FindWindow(None, title)
                if hwnd:
                    rect = win32gui.GetWindowRect(hwnd)
                    return {
                        "success": True,
                        "element": {
                            "role": "Window",
                            "title": title,
                            "position": {"x": rect[0], "y": rect[1]},
                            "size": {"width": rect[2] - rect[0], "height": rect[3] - rect[1]}
                        }
                    }
            
            # Find window by class name if role is specified
            if role:
                hwnd = win32gui.FindWindow(role, None)
                if hwnd:
                    window_text = win32gui.GetWindowText(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    return {
                        "success": True,
                        "element": {
                            "role": role,
                            "title": window_text,
                            "position": {"x": rect[0], "y": rect[1]},
                            "size": {"width": rect[2] - rect[0], "height": rect[3] - rect[1]}
                        }
                    }
            
            return {"success": False, "error": "Element not found"}
            
        except Exception as e:
            logger.error(f"Error finding element: {e}")
            return {"success": False, "error": str(e)}

class WindowsAutomationHandler(BaseAutomationHandler):
    """Windows implementation of automation handler using pyautogui and Windows APIs."""
    
    # Mouse Actions
    async def mouse_down(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.mouseDown(button=button)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def mouse_up(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.mouseUp(button=button)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def move_cursor(self, x: int, y: int) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.moveTo(x, y)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def left_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.click()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.rightClick()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.doubleClick(interval=0.1)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def drag_to(self, x: int, y: int, button: str = "left", duration: float = 0.5) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.dragTo(x, y, duration=duration, button=button)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def drag(self, path: List[Tuple[int, int]], button: str = "left", duration: float = 0.5) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            if not path:
                return {"success": False, "error": "Path is empty"}
            
            # Move to first position
            pyautogui.moveTo(*path[0])
            
            # Drag through all positions
            for x, y in path[1:]:
                pyautogui.dragTo(x, y, duration=duration/len(path), button=button)
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Keyboard Actions
    async def key_down(self, key: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.keyDown(key)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def key_up(self, key: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.keyUp(key)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def type_text(self, text: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.write(text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def press_key(self, key: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.press(key)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def hotkey(self, keys: str) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.hotkey(*keys)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Scrolling Actions
    async def scroll(self, x: int, y: int) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            # pyautogui.scroll() only takes one parameter (vertical scroll)
            pyautogui.scroll(y)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def scroll_down(self, clicks: int = 1) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.scroll(-clicks)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def scroll_up(self, clicks: int = 1) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            pyautogui.scroll(clicks)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Screen Actions
    async def screenshot(self) -> Dict[str, Any]:
        if not pyautogui:
            return {"success": False, "error": "pyautogui not available"}
        
        try:
            from PIL import Image
            screenshot = pyautogui.screenshot()
            if not isinstance(screenshot, Image.Image):
                return {"success": False, "error": "Failed to capture screenshot"}
            
            buffered = BytesIO()
            screenshot.save(buffered, format="PNG", optimize=True)
            buffered.seek(0)
            image_data = base64.b64encode(buffered.getvalue()).decode()
            return {"success": True, "image_data": image_data}
        except Exception as e:
            return {"success": False, "error": f"Screenshot error: {str(e)}"}

    async def get_screen_size(self) -> Dict[str, Any]:
        try:
            if pyautogui:
                size = pyautogui.size()
                return {"success": True, "size": {"width": size.width, "height": size.height}}
            elif WINDOWS_API_AVAILABLE:
                # Fallback to Windows API
                width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                return {"success": True, "size": {"width": width, "height": height}}
            else:
                return {"success": False, "error": "No screen size detection method available"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_cursor_position(self) -> Dict[str, Any]:
        try:
            if pyautogui:
                pos = pyautogui.position()
                return {"success": True, "position": {"x": pos.x, "y": pos.y}}
            elif WINDOWS_API_AVAILABLE:
                # Fallback to Windows API
                pos = win32gui.GetCursorPos()
                return {"success": True, "position": {"x": pos[0], "y": pos[1]}}
            else:
                return {"success": False, "error": "No cursor position detection method available"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Clipboard Actions
    async def copy_to_clipboard(self) -> Dict[str, Any]:
        try:
            import pyperclip
            content = pyperclip.paste()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_clipboard(self, text: str) -> Dict[str, Any]:
        try:
            import pyperclip
            pyperclip.copy(text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Command Execution
    async def run_command(self, command: str) -> Dict[str, Any]:
        try:
            # Use cmd.exe for Windows commands
            process = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return {
                "success": True, 
                "stdout": process.stdout, 
                "stderr": process.stderr, 
                "return_code": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
