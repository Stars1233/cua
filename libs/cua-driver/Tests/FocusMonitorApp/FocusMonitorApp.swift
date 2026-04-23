/// FocusMonitorApp — counts how many times it loses focus.
///
/// On every NSApplication.didResignActiveNotification the counter increments
/// and the current value is written to /tmp/focus_monitor_losses.txt.
/// At startup, prints FOCUS_PID=<pid> to stdout so the test harness can
/// discover the process.

import AppKit

class AppDelegate: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var label: NSTextField!
    var lossCount = 0

    func applicationDidFinishLaunching(_ notification: Notification) {
        let rect = NSRect(x: 200, y: 200, width: 420, height: 200)
        window = NSWindow(
            contentRect: rect,
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.title = "Focus Monitor"
        window.isReleasedWhenClosed = false

        label = NSTextField(labelWithString: "focus_losses: 0")
        label.font = NSFont.monospacedSystemFont(ofSize: 32, weight: .bold)
        label.frame = NSRect(x: 20, y: 60, width: 380, height: 80)
        label.alignment = .center
        window.contentView?.addSubview(label)

        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        NotificationCenter.default.addObserver(
            self,
            selector: #selector(appDidResign),
            name: NSApplication.didResignActiveNotification,
            object: nil
        )

        writeLosses()
        let pid = ProcessInfo.processInfo.processIdentifier
        // Flush to stdout so the test harness can read it.
        print("FOCUS_PID=\(pid)")
        fflush(stdout)
    }

    @objc func appDidResign(_ note: Notification) {
        lossCount += 1
        label.stringValue = "focus_losses: \(lossCount)"
        writeLosses()
    }

    func writeLosses() {
        let path = "/tmp/focus_monitor_losses.txt"
        try? "\(lossCount)".write(toFile: path, atomically: true, encoding: .utf8)
    }
}

// Minimal NSApplication bootstrap — no XIB, no storyboard.
let app = NSApplication.shared
app.setActivationPolicy(.regular)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
