from __future__ import annotations

import unittest

from tools.validate_rdb import MODE_CREATE_INCOMPLETE_MESSAGE, validate_rdb


class TestRelationships(unittest.TestCase):
    def test_placeholder_rdb_is_structurally_valid_but_not_ready(self) -> None:
        result = validate_rdb(__import__("pathlib").Path(__file__).resolve().parents[1])
        self.assertFalse(result.has_critical_errors)
        self.assertFalse(result.mode_create_ready)
        self.assertGreater(len(result.incomplete_files), 0)

    def test_incomplete_message_is_stable(self) -> None:
        self.assertEqual(
            MODE_CREATE_INCOMPLETE_MESSAGE,
            "The HK-RDB is incomplete for this operation. Update the database before continuing.",
        )


if __name__ == "__main__":
    unittest.main()
