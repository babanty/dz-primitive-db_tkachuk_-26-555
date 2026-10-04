import io
import unittest
from contextlib import redirect_stdout

from primitive_db.main import main


class MainTests(unittest.TestCase):
    def test_greeting(self):
        output = io.StringIO()

        with redirect_stdout(output):
            main()

        self.assertEqual(output.getvalue().strip(), "Hello world")
