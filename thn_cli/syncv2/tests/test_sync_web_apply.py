# thn_cli/syncv2/tests/test_sync_web_apply.py

import json
import os
import shutil
import tempfile
import unittest

from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.envelope import load_envelope_from_file
from thn_cli.syncv2.make_test import make_test_envelope
from thn_cli.syncv2.targets.web import WebSyncTarget


class SyncWebApplyTests(unittest.TestCase):
    def setUp(self) -> None:
        # Create a small temp source tree
        self.src_dir = tempfile.mkdtemp(prefix="thn-sync-test-src-")
        with open(os.path.join(self.src_dir, "example.txt"), "w", encoding="utf-8") as f:
            f.write("hello world")

        # Build raw ZIP
        raw_zip = os.path.join(self.src_dir, "payload.zip")
        shutil.make_archive(
            base_name=raw_zip.replace(".zip", ""),
            format="zip",
            root_dir=self.src_dir,
        )
        self.raw_zip = raw_zip

        # Build envelope
        env_result = make_test_envelope(self.raw_zip)
        self.envelope_zip = env_result["envelope_zip"]
        self.envelope = load_envelope_from_file(self.envelope_zip)

        # Per-test destination + backup roots
        self.dest_dir = tempfile.mkdtemp(prefix="thn-sync-test-dest-")
        self.backup_root = tempfile.mkdtemp(prefix="thn-sync-test-backups-")

    def tearDown(self) -> None:
        for path in [self.src_dir, self.dest_dir, self.backup_root]:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)

        if hasattr(self, "envelope_zip") and os.path.exists(self.envelope_zip):
            os.remove(self.envelope_zip)

        if hasattr(self, "raw_zip") and os.path.exists(self.raw_zip):
            os.remove(self.raw_zip)

    def test_dry_run(self) -> None:
        target = WebSyncTarget(
            destination_path=self.dest_dir,
            backup_root=self.backup_root,
        )
        result = apply_envelope_v2(self.envelope, target, dry_run=True)

        self.assertTrue(result["success"])
        self.assertEqual(result["operation"], "dry-run")
        self.assertEqual(result["target"], "web")
        self.assertEqual(result["destination"], self.dest_dir)

        # Ensure no files written
        self.assertEqual(os.listdir(self.dest_dir), [])

    def test_apply_success(self) -> None:
        target = WebSyncTarget(
            destination_path=self.dest_dir,
            backup_root=self.backup_root,
        )
        result = apply_envelope_v2(self.envelope, target, dry_run=False)

        self.assertTrue(result["success"])
        self.assertEqual(result["operation"], "apply")
        self.assertEqual(result["destination"], self.dest_dir)

        # Destination should now contain the extracted file(s)
        contents = os.listdir(self.dest_dir)
        self.assertIn("example.txt", contents)


if __name__ == "__main__":
    unittest.main()
