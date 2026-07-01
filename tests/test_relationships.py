from __future__ import annotations

import unittest

from tools.validate_rdb import MODE_CREATE_INCOMPLETE_MESSAGE, validate_rdb


class TestRelationships(unittest.TestCase):
    def test_released_rdb_is_structurally_valid_and_ready(self) -> None:
        result = validate_rdb(__import__("pathlib").Path(__file__).resolve().parents[1])
        self.assertFalse(result.has_critical_errors)
        self.assertTrue(result.mode_create_ready)
        self.assertEqual(result.incomplete_files, [])

    def test_incomplete_message_is_stable(self) -> None:
        self.assertEqual(
            MODE_CREATE_INCOMPLETE_MESSAGE,
            "The HK-RDB is incomplete for this operation. Update the database before continuing.",
        )


if __name__ == "__main__":
    unittest.main()
