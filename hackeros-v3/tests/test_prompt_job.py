import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "staging/opt/hackeros"))
from prompt_job import PromptJob


class PromptTests(unittest.TestCase):
    def test_output_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            job = PromptJob([sys.executable, "-c", 'print("x" * 50000)'], directory)
            self.assertTrue(job.done.wait(5))
            self.assertEqual(job.process.returncode, 0)
            self.assertLessEqual(len(job.output), 32768)

    def test_cancel(self):
        with tempfile.TemporaryDirectory() as directory:
            job = PromptJob([sys.executable, "-c", "import time; time.sleep(30)"], directory)
            job.cancel()
            self.assertTrue(job.done.wait(5))
            self.assertNotEqual(job.process.returncode, 0)
