import re
import json
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("git_challenge_dir", nargs='?', default=Path.cwd())
args = parser.parse_args()

containers = []

if Path(args.git_challenge_dir).exists():
    challdirs = [Path(args.git_challenge_dir).resolve()]
else:
    challdirs = list(Path('challenges/').glob(args.git_challenge_dir))

assert len(challdirs) > 0, "No challenge found that matches glob"

for challdir in challdirs:
    assert challdir.exists()

    git_challenge_dir = challdir.name
    assert git_challenge_dir.startswith("ctc2024-")

    if (challdir / ".ctfignore").exists():
        continue

    assert not (challdir / "Dockerfile").exists(), f"Dockerfile for {git_challenge_dir} should be in a subdirectory"

    for f in challdir.iterdir():
        if f.is_dir():
            dockerfile = f / "Dockerfile"
            if (dockerfile).exists():
                assert re.fullmatch(r"[a-zA-Z0-9\-]+", f.name)
                containers.append({
                    "dir": f"{git_challenge_dir}/{f.name}",
                    "name": f"{git_challenge_dir}-{f.name}"
                })

print(json.dumps(containers, separators=(',', ':')))

