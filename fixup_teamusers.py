import argparse
import time

from ctfdsync.ctfdapi import CtfdApi

ctfdapi = CtfdApi()

parser = argparse.ArgumentParser()
parser.add_argument('file', type=argparse.FileType('r'))
args = parser.parse_args()

print("[X] Perform user to team joins. Preview:")

teams = {}

for line in args.file.readlines():
	line = line.strip()
	if len(line) == 0:
		continue
	
	userid, teamid = map(int, line.split(" "))
	
	if teamid not in teams:
		teams[teamid] = []
	
	teams[teamid].append(userid)

sorted_teams = dict(sorted(teams.items()))

for teamid, users in sorted_teams.items():
	print(f"Team {teamid} will have users: {users}")

input("Continue? Or Ctrl-C")


for i in range(3, 0, -1):
	print(i)
	time.sleep(1)
	
for teamid, users in sorted_teams.items():
	print()
	print (f"[+] Looping Team {teamid}:")
	for userid in users:
		req = ctfdapi.post(f"teams/{teamid}/members", json={"user_id": userid})
		status = "OK" if req.ok else "FAIL"
		print(f"Joining User {userid} to Team {teamid} - {status}")

print()
print("[X] Done!")
