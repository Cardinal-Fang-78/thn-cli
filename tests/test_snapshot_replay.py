from __future__ import annotations

from thn_cli.presentation.replay import compute_replay_tree
from thn_cli.snapshots.diff_engine import diff_snapshots


def test_replay_no_changes_is_identity():
    snap = {
        "schema_version": 1,
        "id": "0001",
        "tree": ["README.md", "src/app.py", "src/lib/util.py"],
    }

    diff = diff_snapshots(before=snap, after=snap)
    replayed = compute_replay_tree(snapshot=snap, diff=diff)

    assert replayed == sorted(["README.md", "src/app.py", "src/lib/util.py"])


def test_replay_adds_paths():
    before = {
        "schema_version": 1,
        "id": "0001",
        "tree": ["README.md", "src/app.py"],
    }
    after = {
        "schema_version": 1,
        "id": "0002",
        "tree": ["README.md", "src/app.py", "src/new_feature.py"],
    }

    diff = diff_snapshots(before=before, after=after)
    replayed = compute_replay_tree(snapshot=before, diff=diff)

    assert replayed == sorted(["README.md", "src/app.py", "src/new_feature.py"])


def test_replay_removes_paths():
    before = {
        "schema_version": 1,
        "id": "0001",
        "tree": ["README.md", "src/app.py", "src/lib/util.py"],
    }
    after = {
        "schema_version": 1,
        "id": "0002",
        "tree": ["README.md", "src/app.py"],
    }

    diff = diff_snapshots(before=before, after=after)
    replayed = compute_replay_tree(snapshot=before, diff=diff)

    assert replayed == sorted(["README.md", "src/app.py"])


def test_replay_mixed_changes_matches_after_tree():
    before = {
        "schema_version": 1,
        "id": "0001",
        "tree": ["README.md", "src/app.py", "src/lib/util.py"],
    }
    after = {
        "schema_version": 1,
        "id": "0002",
        "tree": ["README.md", "src/app.py", "src/new_feature.py", "src/legacy/old.py"],
    }

    diff = diff_snapshots(before=before, after=after)
    replayed = compute_replay_tree(snapshot=before, diff=diff)

    assert replayed == sorted(
        ["README.md", "src/app.py", "src/new_feature.py", "src/legacy/old.py"]
    )


def test_replay_normalizes_paths_and_deduplicates():
    before = {
        "schema_version": 1,
        "id": "0001",
        "tree": ["README.md", "src\\app.py", "./src/lib/util.py", "src/lib/util.py"],
    }
    after = {
        "schema_version": 1,
        "id": "0002",
        "tree": ["README.md", "src/app.py", "src/new_feature.py"],
    }

    diff = diff_snapshots(before=before, after=after)
    replayed = compute_replay_tree(snapshot=before, diff=diff)

    assert replayed == sorted(["README.md", "src/app.py", "src/new_feature.py"])
