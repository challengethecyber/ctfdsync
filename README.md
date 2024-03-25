# ctfdsync
Poor man's ctfd sync... Not a finished product.
... Do not use unless you have a need to :-)

- Custom yaml format
  - Supports subtasks
  - Hijacks 'category' in ctfd for the challenge name. Subtask name is set as the challenge name.
  - Supports files and updates to files
- Stateless
  - (Ab)uses 'topics' in CTFd to store metadata about challenges (as a very poorly implemented key-value store)
  - Allows to keep track which challenge directory in git maps to a challenge in ctfd
- Synchronizes challenge yamls from a directory structure into a live CTFd instance
