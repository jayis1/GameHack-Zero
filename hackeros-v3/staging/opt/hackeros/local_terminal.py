"""Controller-operated local PTY terminal with a shallow coding keyboard."""
import codecs
import errno
import fcntl
import os
import pty
import signal
import struct
import termios
import time


ROWS = [list('1234567890-='), list('qwertyuiop[]'), list("asdfghjkl;'\\"),
        list('zxcvbnm,./` '),
        ['Shift', 'Space', 'Back', 'Enter', 'Tab', 'Esc', 'Ctrl', 'Left', 'Down', 'Up', 'Right', 'Hide']]
SHIFTED = dict(zip('1234567890-=[];\'\\,./`', '!@#$%^&*()_+{}:"|<>?~'))
KEYS = {'Space': ' ', 'Back': '\x7f', 'Enter': '\r', 'Tab': '\t', 'Esc': '\x1b',
        'Left': '\x1b[D', 'Down': '\x1b[B', 'Up': '\x1b[A', 'Right': '\x1b[C'}


class CodingKeyboard:
    def __init__(self):
        self.row = self.col = 0
        self.shift = self.ctrl = False

    def move(self, action):
        if action in ('up', 'down'):
            self.row = (self.row + (1 if action == 'down' else -1)) % len(ROWS)
        else:
            self.col = (self.col + (1 if action == 'right' else -1)) % 12

    def label(self, key):
        return SHIFTED.get(key, key.upper()) if self.shift and len(key) == 1 else key

    def press(self, key=None):
        key = key or ROWS[self.row][self.col]
        if key == 'Shift':
            self.shift = not self.shift
            return b''
        if key == 'Ctrl':
            self.ctrl = not self.ctrl
            return b''
        text = KEYS.get(key, self.label(key))
        if self.ctrl and len(text) == 1:
            text = chr(ord(text.upper()) & 31)
            self.ctrl = False
        return text.encode('utf-8')


class LocalPTY:
    def __init__(self, command, directory, columns, lines):
        import pyte
        session = self
        class ReplyScreen(pyte.Screen):
            def write_process_input(self, data):
                session.write(data.encode())
        self.screen = ReplyScreen(columns, lines)
        self.stream = pyte.Stream(self.screen)
        self.decoder = codecs.getincrementaldecoder('utf-8')('replace')
        self.status = None
        self.eof = False
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            try:
                os.chdir(directory)
                os.execvpe(command[0], command, dict(os.environ, TERM='xterm-256color', COLORTERM='truecolor'))
            except Exception as exc:
                os.write(2, ('Terminal startup failed: ' + str(exc) + '\r\n').encode())
                os._exit(127)
        os.set_blocking(self.fd, False)
        self.resize(columns, lines)

    def resize(self, columns, lines):
        self.screen.resize(lines=lines, columns=columns)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack('HHHH', lines, columns, 0, 0))

    def write(self, data):
        if not self.eof:
            try:
                os.write(self.fd, data)
            except OSError as exc:
                if exc.errno not in (errno.EIO, errno.EBADF, errno.EAGAIN):
                    raise

    def poll(self):
        for _ in range(16):
            try:
                data = os.read(self.fd, 4096)
            except BlockingIOError:
                break
            except OSError as exc:
                if exc.errno != errno.EIO:
                    raise
                data = b''
            if not data:
                if not self.eof:
                    self.stream.feed(self.decoder.decode(b'', final=True))
                self.eof = True
                break
            self.stream.feed(self.decoder.decode(data))
        if self.status is None:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                self.status = os.waitstatus_to_exitcode(status)

    def close(self):
        try:
            if self.status is None:
                try:
                    os.killpg(self.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                for _ in range(30):
                    pid, status = os.waitpid(self.pid, os.WNOHANG)
                    if pid:
                        self.status = os.waitstatus_to_exitcode(status)
                        break
                    time.sleep(0.05)
                if self.status is None:
                    os.killpg(self.pid, signal.SIGKILL)
                    _, status = os.waitpid(self.pid, 0)
                    self.status = os.waitstatus_to_exitcode(status)
        finally:
            os.close(self.fd)


COLORS = {'black': (0, 0, 0), 'red': (210, 85, 85), 'green': (125, 200, 120),
          'brown': (210, 175, 95), 'yellow': (210, 175, 95), 'blue': (100, 155, 220),
          'magenta': (185, 135, 210), 'cyan': (100, 195, 200), 'white': (225, 225, 225)}


def color(value, default):
    if value in COLORS:
        return COLORS[value]
    if len(value) == 6:
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default


class TerminalView:
    def __init__(self, ui, title):
        import pygame
        self.ui, self.title = ui, title
        self.keyboard = CodingKeyboard()
        self.visible = True
        self.font = pygame.font.Font('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 12)
        self.labels = pygame.font.Font('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 11)
        self.cw, self.ch = self.font.size('M')[0], self.font.get_linesize()
        self.cache = {}

    def dimensions(self):
        return max(20, self.ui.width // self.cw), max(8, (self.ui.height - 24 - (112 if self.visible else 20)) // self.ch)

    def draw(self, screen, status=None):
        import pygame
        surface = self.ui.screen
        surface.fill((12, 14, 18))
        header = self.title + (' / EXIT ' + str(status) if status is not None else ' / LOCAL')
        surface.blit(self.labels.render(header, True, (235, 180, 75)), (5, 4))
        for row in range(screen.lines):
            for col in range(screen.columns):
                cell = screen.buffer[row][col]
                fg = color(cell.fg, (225, 225, 225))
                bg = color(cell.bg, (12, 14, 18))
                if cell.reverse:
                    fg, bg = bg, fg
                rect = (col * self.cw, 24 + row * self.ch, self.cw, self.ch)
                if bg != (12, 14, 18):
                    pygame.draw.rect(surface, bg, rect)
                if cell.data.strip():
                    key = (cell.data, fg, cell.bold)
                    if key not in self.cache:
                        if len(self.cache) > 2048:
                            self.cache.clear()
                        self.font.set_bold(cell.bold)
                        self.cache[key] = self.font.render(cell.data, True, fg)
                    surface.blit(self.cache[key], rect[:2])
        if not screen.cursor.hidden:
            pygame.draw.rect(surface, (235, 180, 75), (screen.cursor.x * self.cw, 24 + (screen.cursor.y + 1) * self.ch - 2, self.cw, 2))
        top = self.ui.height - 112
        if self.visible:
            width = self.ui.width / 12
            for row, keys in enumerate(ROWS):
                for col, key in enumerate(keys):
                    selected = (row, col) == (self.keyboard.row, self.keyboard.col)
                    rect = pygame.Rect(int(col * width), top + row * 19, int(width) - 1, 18)
                    pygame.draw.rect(surface, (90, 66, 28) if selected else (27, 30, 36), rect)
                    text = self.labels.render(self.keyboard.label(key), True, (255, 220, 150) if selected else (195, 200, 205))
                    surface.blit(text, text.get_rect(center=rect.center))
        hint = 'R2:type  L2:back  Y:keys  X:shortcuts'
        if self.keyboard.shift:
            hint += ' SHIFT'
        if self.keyboard.ctrl:
            hint += ' CTRL'
        surface.blit(self.labels.render(hint, True, (150, 155, 165)), (5, self.ui.height - 16))
        pygame.display.flip()


def run_terminal(ui, command, directory, title='OPENCODE'):
    import pygame
    view = TerminalView(ui, title)
    session = LocalPTY(command, directory, *view.dimensions())
    shortcuts = {'Enter': b'\r', 'Escape / interrupt': b'\x1b', 'Command palette': b'\x10',
                 'Tab / autocomplete': b'\t', 'Page up': b'\x1b[5~', 'Page down': b'\x1b[6~',
                 'Ctrl+C': b'\x03', 'Ctrl+D': b'\x04', 'Ctrl+X (leader)': b'\x18'}
    try:
        while True:
            session.poll()
            view.draw(session.screen, session.status)
            action = ui.get_action()
            if action == 'back':
                if session.status is not None or ui.confirm('LEAVE LOCAL TERMINAL?', 'Close this terminal client?\nOpenCode may have a separate background service.\nSaved files and sessions are not erased.'):
                    return
            elif action in ('up', 'down', 'left', 'right'):
                if view.visible:
                    view.keyboard.move(action)
                else:
                    session.write(KEYS[action.title()].encode())
            elif action == 'confirm':
                if not view.visible:
                    session.write(b'\r')
                elif ROWS[view.keyboard.row][view.keyboard.col] == 'Hide':
                    view.visible = False
                    session.resize(*view.dimensions())
                else:
                    session.write(view.keyboard.press())
            elif action == 'details':
                view.visible = not view.visible
                session.resize(*view.dimensions())
            elif action == 'status':
                chosen = ui.select('TERMINAL SHORTCUTS', list(shortcuts))
                if chosen:
                    session.write(shortcuts[chosen])
            time.sleep(0.03)
    finally:
        session.close()
        while not ui.events.empty():
            ui.events.get_nowait()
