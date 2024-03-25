import re
import json
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("git_challenge_dir", nargs='?', default=Path.cwd())
args = parser.parse_args()

challenges = []

if Path(args.git_challenge_dir).exists():
    challdirs = [Path(args.git_challenge_dir).resolve()]
else:
    challdirs = list(Path('challenges/').glob(args.git_challenge_dir))

assert len(challdirs) > 0, "No challenge found that matches glob"

for challdir in challdirs:
    assert challdir.exists()

    git_challenge_dir = challdir.name
    assert git_challenge_dir.startswith("ctc2023-")

    if (challdir / ".ctfignore").exists():
        continue

    challenges.append({"dir": git_challenge_dir})

print(json.dumps(challenges, separators=(',', ':')))
