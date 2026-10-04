"""Shared isolated database test fixture."""

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.previous_directory = os.getcwd()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)

        os.chdir(self.temporary_directory.name)
        self.addCleanup(os.chdir, self.previous_directory)

        self.output = io.StringIO()
        output_redirect = redirect_stdout(self.output)
        output_redirect.__enter__()
        self.addCleanup(output_redirect.__exit__, None, None, None)

        confirmation = patch("builtins.input", return_value="y")
        confirmation.start()
        self.addCleanup(confirmation.stop)
