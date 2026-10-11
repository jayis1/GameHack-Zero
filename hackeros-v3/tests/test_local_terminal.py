import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'staging/opt/hackeros'))
import local_terminal as terminal


class TerminalTests(unittest.TestCase):
    def test_compact_key_layers(self):
        keyboard = terminal.CodingKeyboard()
        self.assertTrue(all(len(row) == 12 for row in terminal.ROWS))
        self.assertEqual(keyboard.press('a'), b'a')
        keyboard.press('Shift')
        self.assertEqual(keyboard.press('a'), b'A')
        self.assertEqual(keyboard.press('['), b'{')
        self.assertEqual(keyboard.press('\\'), b'|')
        keyboard.press('Ctrl')
        self.assertEqual(keyboard.press('p'), b'\x10')
        self.assertFalse(keyboard.ctrl)
        self.assertEqual(keyboard.press('Enter'), b'\r')
        self.assertEqual(keyboard.press('Back'), b'\x7f')

    def test_wrap_navigation(self):
        keyboard = terminal.CodingKeyboard()
        keyboard.move('left')
        self.assertEqual(keyboard.col, 11)
        keyboard.move('up')
        self.assertEqual(keyboard.row, 4)

    def test_actual_local_pty_ansi_and_resize(self):
        with tempfile.TemporaryDirectory() as folder:
            session = terminal.LocalPTY([sys.executable, '-c', 'import os,time; print("\\x1b[32mLOCAL-PTY\\x1b[0m",flush=True); time.sleep(.1)'], folder, 80, 20)
            try:
                for _ in range(100):
                    session.poll()
                    if session.status is not None and session.eof:
                        break
                    time.sleep(.01)
                self.assertEqual(session.status, 0)
                self.assertIn('LOCAL-PTY', '\n'.join(session.screen.display))
                self.assertEqual(session.screen.buffer[0][0].fg, 'green')
                session.resize(90, 25)
                self.assertEqual((session.screen.columns, session.screen.lines), (90, 25))
            finally:
                session.close()

    def test_terminal_device_queries_get_reply(self):
        code = 'import os,tty; tty.setraw(0); os.write(1,b"\\x1b[6n"); r=os.read(0,100); os.write(1,b"REPLIED" if r.startswith(b"\\x1b[") else b"BAD")'
        session = terminal.LocalPTY([sys.executable, '-c', code], '/tmp/opencode', 80, 20)
        try:
            for _ in range(100):
                session.poll()
                if session.status is not None and session.eof:
                    break
                time.sleep(.01)
            self.assertEqual(session.status, 0)
            self.assertIn('REPLIED', '\n'.join(session.screen.display))
        finally:
            session.close()

    def test_child_exec_failure_is_visible(self):
        session = terminal.LocalPTY(['/nonexistent/gamehack-test-binary'], '/tmp/opencode', 80, 20)
        try:
            for _ in range(100):
                session.poll()
                if session.status is not None and session.eof:
                    break
                time.sleep(.01)
            self.assertEqual(session.status, 127)
            self.assertIn('startup failed', '\n'.join(session.screen.display))
        finally:
            session.close()

    def test_keyboard_dock_render(self):
        import pygame
        import pyte
        pygame.display.init()
        pygame.font.init()
        surface = pygame.display.set_mode((640, 480))
        ui = SimpleNamespace(screen=surface, width=640, height=480)
        font = pygame.font.Font
        def fallback(path, size):
            return font(path if Path(path).exists() else str(Path('/usr/share/fonts/TTF') / Path(path).name), size)
        try:
            with patch.object(pygame.font, 'Font', side_effect=fallback):
                view = terminal.TerminalView(ui, 'OPENCODE / LAYOUT PREVIEW')
            columns, lines = view.dimensions()
            screen = pyte.Screen(columns, lines)
            pyte.Stream(screen).feed('GameHack Zero local coding terminal\r\n\r\nPTY + controller keyboard layout test (not a live OpenCode session)\r\n\r\nWorkspace: /data/gamehack-zero/projects\r\n\r\n> Explain this project and help edit main.py\r\n\r\nY: hide keyboard for more code space\r\nX: command palette / paging / interrupt\r\n')
            view.draw(screen)
            pygame.image.save(surface, '/tmp/opencode/gamehack-opencode-terminal-preview.png')
            self.assertGreater(columns, 70)
            self.assertGreater(lines, 15)
            view.visible = False
            self.assertGreater(view.dimensions()[1], lines)
        finally:
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
