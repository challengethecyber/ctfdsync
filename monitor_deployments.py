import csv
import collections
from io import StringIO
from ctfdsync.ctfdapi import CtfdApi

ctfdapi = CtfdApi()

req = ctfdapi.get("admin/export/csv?table=container_log", omit_prefix=True)
assert req.ok

reader = csv.DictReader(StringIO(req.text))

user_deploys = collections.defaultdict(list)
user_maxepoch = collections.defaultdict(int)

for row in reader:
    user_id = int(row['user_id'])
    chall_id = int(row['challenge_id'])
    start_epoch = int(row['start_epoch'])

    user_deploys[user_id].append((chall_id, start_epoch))
    user_maxepoch[user_id] = max(user_maxepoch[user_id], start_epoch)

for user_id, deployments in user_deploys.items():

    if len(deployments) > 1:
        for chall_id, start_epoch in deployments:
            if start_epoch < user_maxepoch[user_id]:
                print(f"[*] Removing stale deployment: user_id={user_id} chall_id={chall_id} start_epoch={start_epoch}")
                req = ctfdapi.delete("container_challenges/namespace", omit_prefix=True, json={
                    "challenge_id": str(chall_id),
                    "user_id": str(user_id)
                })
                print("\tOK" if req.ok else "\tFAIL")
