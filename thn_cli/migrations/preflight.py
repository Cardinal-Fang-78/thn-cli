from __future__ import annotations

from pathlib import Path

from thn_cli.pathing import get_thn_paths
from thn_cli.post_make.context import PostMakeContext
from thn_cli.post_make.errors import PostMakeVerificationError
from thn_cli.post_make.verifier import verify_make_output


def ensure_clean_or_forced(*, root: Path, force: bool) -> None:
    """
    Refuse migration if scaffold is drifted unless --force is supplied.
    """
    if force:
        return

    ctx = PostMakeContext(
        command="migrate scaffold",
        project="",
        target_kind="scaffold",
        target_name=str(root),
        blueprint_id="",
        thn_paths=get_thn_paths(),
        output_path=str(root),
    )

    try:
        verify_make_output(ctx)
    except PostMakeVerificationError as exc:
        raise PostMakeVerificationError(
            "Migration refused: scaffold has unaccepted drift.\n"
            "Run `thn inspect scaffold` to review, or use --force to override.\n"
            f"Details: {exc}"
        )
