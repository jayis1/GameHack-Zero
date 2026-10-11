# Local GameHack coding

DEVELOP > OpenCode / local coding TUI runs the real interactive OpenCode client
directly on the handheld as hacker, inside /data/gamehack-zero/projects.
This is a controller/PTY terminal frontend, not an OpenCode fork or SSH client.
The existing quick-prompt workflow remains available separately.

Keyboard dock is 112 pixels high on the 640x480 display. Four character rows
and one control row include digits, lowercase/uppercase, coding punctuation,
Space, Backspace, Enter, Tab, Escape, Ctrl and arrow keys. D-pad moves selection;
R2/A types/selects; L2/B asks to leave. Y hides/shows the dock. When hidden,
D-pad sends terminal arrow keys and R2 sends Enter. X opens terminal shortcuts
(command palette, interrupt, paging, autocomplete, Ctrl+C/D/X). Ctrl applies
to the next single-character key; Shift is a persistent layer. Leave does not
erase files, sessions or credentials and does not stop a shared OpenCode service.

Run /connect inside OpenCode to configure your own provider. API-key providers
can be configured through the keyboard; OAuth may require visiting a browser
URL on another device. No SSH required to operate the TUI. On-device execution
does not mean offline inference: cloud providers still need Wi-Fi/internet.
No PC provider credentials are copied. Permissions stay under OpenCode control;
requests are not autoaccepted by this frontend.

Local coding terminal also runs bash without login profiles and supports tools
such as nano in the same workspace. It has the same compact keyboard.

Dependency: Debian python3-pyte; nano recommended. Parser handles ordinary
ANSI terminal output, cursor/device-status queries and UTF-8. Advanced terminal
protocols, alternate-screen history, clipboard transfer and browser OAuth are
not full desktop-terminal equivalents. OpenCode 2.0.6 native startup remains
unverified; its earlier QEMU runtime crash is not treated as a handheld result.
Test native rendering, dialogs, permissions and provider sign-in before calling
the integration finished. Keep the existing launcher/quick-prompt fallback.

ZERO-DAY-PORT.md and zeroday-features.json inventory upstream features with
explicit adapted/staged/pending/excluded statuses. No fake installed-tool claims.
