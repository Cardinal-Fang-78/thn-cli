# thn_cli/syncv2/tests/manual_demo_apply_web.py

import os
import tempfile
import shutil

from thn_cli.syncv2.make_test import make_test_envelope
from thn_cli.syncv2.envelope import load_envelope_from_file
from thn_cli.syncv2.engine import apply_envelope_v2
from thn_cli.syncv2.targets.web import WebSyncTarget


def main() -> None:
    src_dir = tempfile.mkdtemp(prefix="thn-sync-manual-src-")
    with open(os.path.join(src_dir, "demo.txt"), "w", encoding="utf-8") as f:
        f.write("THN Sync manual demo")

    raw_zip = os.path.join(src_dir, "payload.zip")
    shutil.make_archive(
        base_name=raw_zip.replace(".zip", ""),
        format="zip",
        root_dir=src_dir,
    )

    env_result = make_test_envelope(raw_zip)
    envelope_zip = env_result["envelope_zip"]
    envelope = load_envelope_from_file(envelope_zip)

    dest_dir = tempfile.mkdtemp(prefix="thn-sync-manual-dest-")
    backup_root = tempfile.mkdtemp(prefix="thn-sync-manual-backups-")

    target = WebSyncTarget(destination_path=dest_dir, backup_root=backup_root)

    print("=== DRY RUN ===")
    dry = apply_envelope_v2(envelope, target, dry_run=True)
    print(dry)

    print("\n=== APPLY ===")
    real = apply_envelope_v2(envelope, target, dry_run=False)
    print(real)

    print("\nDestination contents:", os.listdir(dest_dir))

    # Cleanup for demo; comment out if you want to inspect the result.
    shutil.rmtree(src_dir, ignore_errors=True)
    shutil.rmtree(dest_dir, ignore_errors=True)
    shutil.rmtree(backup_root, ignore_errors=True)
    if os.path.exists(envelope_zip):
        os.remove(envelope_zip)
    if os.path.exists(raw_zip):
        os.remove(raw_zip)


if __name__ == "__main__":
    main()
