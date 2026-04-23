import CoreGraphics
import CuaDriverCore
import Foundation
import MCP

public enum SetValueTool {
    public static let handler = ToolHandler(
        tool: Tool(
            name: "set_value",
            description: """
                Directly set an element's AXValue attribute. For controls like sliders,
                steppers, and text fields that expose a settable value. Accepts a string
                (which the target element will coerce as needed).

                For free-form text entry, prefer `type_text_in` — it inserts at the
                cursor rather than replacing the whole value.
                """,
            inputSchema: [
                "type": "object",
                "required": ["pid", "window_id", "element_index", "value"],
                "properties": [
                    "pid": ["type": "integer"],
                    "window_id": [
                        "type": "integer",
                        "description":
                            "CGWindowID for the window whose get_window_state produced the element_index. The element_index cache is scoped per (pid, window_id).",
                    ],
                    "element_index": ["type": "integer"],
                    "value": [
                        "type": "string",
                        "description":
                            "New value. AX will coerce to the element's native type.",
                    ],
                ],
                "additionalProperties": false,
            ],
            annotations: .init(
                readOnlyHint: false,
                destructiveHint: true,
                idempotentHint: true,  // setting same value twice is idempotent
                openWorldHint: true
            )
        ),
        invoke: { arguments in
            guard
                let rawPid = arguments?["pid"]?.intValue,
                let rawWindowId = arguments?["window_id"]?.intValue,
                let index = arguments?["element_index"]?.intValue
            else {
                return errorResult(
                    "Missing required integer fields pid, window_id, and element_index.")
            }
            guard let value = arguments?["value"]?.stringValue else {
                return errorResult("Missing required string field value.")
            }

            guard let pid = Int32(exactly: rawPid) else {
                return errorResult(
                    "pid \(rawPid) is outside the supported Int32 range.")
            }
            guard let windowId = UInt32(exactly: rawWindowId) else {
                return errorResult(
                    "window_id \(rawWindowId) is outside the supported UInt32 range.")
            }
            do {
                let element = try await AppStateRegistry.engine.lookup(
                    pid: pid,
                    windowId: windowId,
                    elementIndex: index
                )
                try await AppStateRegistry.focusGuard.withFocusSuppressed(
                    pid: pid,
                    element: element
                ) {
                    try AXInput.setAttribute(
                        "AXValue",
                        on: element,
                        value: value as CFTypeRef
                    )
                }
                let target = AXInput.describe(element)
                let summary =
                    "✅ Set AXValue on [\(index)] \(target.role ?? "?") \"\(target.title ?? "")\"."
                return CallTool.Result(
                    content: [.text(text: summary, annotations: nil, _meta: nil)]
                )
            } catch let error as AppStateError {
                return errorResult(error.description)
            } catch let error as AXInputError {
                return errorResult(error.description)
            } catch {
                return errorResult("Unexpected error: \(error)")
            }
        }
    )

    private static func isWindowMinimized(pid: Int32) -> Bool {
        guard let onScreen = CGWindowListCopyWindowInfo(
            [.optionOnScreenOnly, .excludeDesktopElements],
            kCGNullWindowID
        ) as? [[String: Any]] else { return false }
        let hasOnScreen = onScreen.contains {
            ($0[kCGWindowOwnerPID as String] as? Int32) == pid
        }
        if hasOnScreen { return false }
        guard let all = CGWindowListCopyWindowInfo(
            [.optionAll], kCGNullWindowID
        ) as? [[String: Any]] else { return false }
        return all.contains {
            ($0[kCGWindowOwnerPID as String] as? Int32) == pid
            && ($0[kCGWindowLayer as String] as? Int32) == 0
        }
    }

    private static func errorResult(_ message: String) -> CallTool.Result {
        CallTool.Result(
            content: [.text(text: message, annotations: nil, _meta: nil)],
            isError: true
        )
    }
}
