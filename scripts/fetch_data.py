import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "dataset" / "raw"

REPOS = {
    "bipia": {
        "url": "https://github.com/microsoft/BIPIA.git",
        "keep": {
            "benchmark/email": "email",
            "benchmark/table": "table",
            "benchmark/code": "code",
            "benchmark/text_attack_train.json": "text_attack_train.json",
            "benchmark/text_attack_test.json": "text_attack_test.json",
            "benchmark/code_attack_train.json": "code_attack_train.json",
            "benchmark/code_attack_test.json": "code_attack_test.json",
        },
    },
    "injecagent": {
        "url": "https://github.com/uiuc-kang-lab/InjecAgent.git",
        "keep": {
            "data": ".",
        },
    },
}


def _handle_readonly(func, path: str, _exc) -> None:
    """Git marks object pack files read-only on Windows; clear the bit before deleting."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_handle_readonly)
    else:
        shutil.rmtree(path, onerror=_handle_readonly)


def copy_selected(clone_dir: Path, target_dir: Path, keep_map: dict[str, str]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for src_rel, dst_rel in keep_map.items():
        src = clone_dir / src_rel
        if not src.exists():
            raise FileNotFoundError(f"Expected path not found in cloned repo: {src_rel}")

        dst = target_dir if dst_rel == "." else target_dir / dst_rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def fetch_repo(name: str, cfg: dict, force: bool) -> None:
    target = RAW_DIR / name
    if target.exists():
        if not force:
            print(f"[skip] {target} already exists (use --force to re-download).")
            return
        print(f"[clean] Removing existing {target}")
        remove_tree(target)

    tmp_dir = Path(tempfile.mkdtemp(prefix=f"{name}_clone_"))
    try:
        print(f"[clone] {cfg['url']} (temporary)")
        subprocess.run(
            ["git", "clone", "--depth", "1", cfg["url"], str(tmp_dir)],
            check=True,
        )
        print(f"[extract] Copying selected files -> {target}")
        copy_selected(tmp_dir, target, cfg["keep"])
    except Exception:
        remove_tree(target)  # Avoid leaving half-copied directories on failure
        raise
    finally:
        remove_tree(tmp_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch only required BIPIA and InjecAgent files.")
    parser.add_argument("--force", action="store_true", help="Delete and re-download existing folders.")
    args = parser.parse_args()

    if shutil.which("git") is None:
        sys.exit("Error: 'git' is not installed or not on PATH.")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for name, cfg in REPOS.items():
        fetch_repo(name, cfg, force=args.force)

    print(f"\nDone. Clean raw datasets ready in: {RAW_DIR}")


if __name__ == "__main__":
    main()