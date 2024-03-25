import os
from pathlib import Path
import shutil
from time import localtime, strftime

path_static = Path(__file__).parent.resolve() / "__static__/"

prefix = (path_static / "prefix.tpl").read_bytes()
suffix = (path_static / "suffix.tpl").read_bytes()

prefix = prefix.replace(b'##TIME##', strftime("%Y-%m-%d %H:%M", localtime()).encode())

assert not (path_static / "output").exists()

for input_file in (path_static / "input").iterdir():
    file_name = input_file.name

    # exception for index
    has_subdir = "___" in file_name

    parts = file_name.split("___")
    dirs = "/".join(parts[:-1])
    new_file = "/".join(parts)

    dest_base = path_static / 'output'

    os.makedirs(dest_base / dirs, exist_ok=True)

    target_file = dest_base / new_file
    shutil.copy(input_file, dest_base / new_file)

    if not has_subdir and target_file.suffix == ".html":
        orig_bytes = target_file.read_bytes()

        if file_name != "challenges.html":
            orig_bytes = b'<main><div class="container"><div id="challenge-window" class="modal show"><div class="modal-dialog"><div class="modal-content"><div class="modal-body">' + orig_bytes
            orig_bytes += b'</div></div></div></div></main>'

        target_file.write_bytes(prefix + orig_bytes + suffix)

shutil.move(dest_base / "challenges.html", dest_base / "index.html")