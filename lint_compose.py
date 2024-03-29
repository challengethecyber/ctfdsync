import sys
import yaml
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("git_challenge_dir", nargs='?', default=Path.cwd())
args = parser.parse_args()

challdir = Path(args.git_challenge_dir)
assert challdir.exists()

git_challenge_dir = challdir.name
assert git_challenge_dir.startswith("ctc2024-")

assert not (challdir / "docker-compose.yml").exists(), "docker-compose extension should be .yaml for consistency"
yamlfile = challdir / "docker-compose.yaml"
yamlfile = yamlfile.resolve()

if not yamlfile.exists():
    sys.exit(0)

assert yamlfile.exists()
yml = yaml.safe_load(yamlfile.open())

assert str(yml['version']) == "3.3", "Version should be 3.3 for consistency"

for service,props in yml['services'].items():
    assert service.startswith(git_challenge_dir)
    assert service != git_challenge_dir, "Service should include container name / subdir"
    
    containerdir = service.split(git_challenge_dir)[1]
    assert containerdir.startswith("-")
    containerdir = containerdir[1:]

    print (challdir / containerdir / "Dockerfile")
    assert (challdir / containerdir / "Dockerfile").exists()

    assert props["container_name"] == service
    print(f"ghcr.io/challengethecyber/{service}:latest")
    assert props["image"] == f"ghcr.io/challengethecyber/{service}:latest"
    
