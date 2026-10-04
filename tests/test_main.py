import unittest
from unittest.mock import patch

from primitive_db.main import main


class MainTests(unittest.TestCase):
    def test_entry_point_starts_engine(self):
        with patch("primitive_db.main.run") as run:
            main()

        run.assert_called_once_with()
