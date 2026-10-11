import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
sys.path.insert(0, '/opt/hackeros')
import launcher

with tempfile.TemporaryDirectory() as folder, patch.object(launcher, 'RESULTS', Path(folder)), patch.object(launcher.threading.Thread, 'start'):
    ui = launcher.GameHackZero()
    assert launcher.pygame.mixer.get_init() is None
    calls = []
    with patch.object(launcher.Path, 'is_file', return_value=True), patch.object(launcher.pygame.mixer, 'quit', side_effect=lambda: calls.append('release audio')), patch.object(launcher.subprocess, 'call', side_effect=lambda *args, **kwargs: calls.append('spawn game') or 0):
        ui.freedoom(1)
    assert calls == ['release audio', 'spawn game']
    ui.draw()
    assert launcher.pygame.mixer.get_init() is None
launcher.pygame.quit()
print('Installed launcher leaves ALSA free and releases audio before spawning Freedoom.')
