import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "dataset" / "raw"
 
REPOS = {
    "bipia" : "https://github.com/microsoft/BIPIA.git",
    "injecagent" : "https://github.com/uiuc-kang-lab/InjecAgent.git",
}

def main() -> None:
    if shutil.which("git") is None:
        sys.exit("Error: 'git' is not installed or not on PATH.")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for folder_name, url in REPOS.items():
        target = RAW_DIR / folder_name
        if target.exists():
            print(f"[skip] {target} already exists.")
            continue
        print(f"[clone] {url} -> {target}")
        subprocess.run(["git", "clone", "--depth", "1", url, str(target)],check=True)
    print("\nDone. Raw datasets are ready in:", RAW_DIR)
        
if __name__ == "__main__":
    main()