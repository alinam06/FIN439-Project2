"""Keep classroom UI regressions independent of optional licensed local data."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


class CleanCheckout(unittest.TestCase):
    def setUp(self):
        super().setUp()
        root = self.enterContext(TemporaryDirectory())
        self.enterContext(patch("src.data_workspace.DATA_DIR", Path(root)))
