import argparse
from pathlib import Path
from ctfdsync.models import *
from ctfdsync.functions import *
from ctfdsync.ctfdapi import CtfdApi

ctfdapi = CtfdApi()

parser = argparse.ArgumentParser()
parser.add_argument("git_challenge_dir", nargs='?', default=Path.cwd())
args = parser.parse_args()

challdir = Path(args.git_challenge_dir)
assert challdir.exists()

git_challenge_dir = challdir.name
assert git_challenge_dir.startswith("ctc2023-")

yamlfile = challdir / "challenge.yaml"
assert yamlfile.exists()

challenge = Challenge.from_yaml(yamlfile)
dirty = False

# Step 1, create missing challenge mappings and remove redundant ones

mappings = get_mappings(git_challenge_dir)

for task_id, task in enumerate(challenge.challenge_tasks, 1):
	mapped_tasks = list(filter(lambda c: c.task_id == task_id, mappings))
	assert len(mapped_tasks) <= 1, "Inconsistent state"
	
	if len(mapped_tasks) == 0:
		create_challenge_for_task(git_challenge_dir, task_id)
		dirty = True

for redundant_entry in filter(lambda c: c.task_id > len(challenge.challenge_tasks), mappings):
	delete_challenge_with_mapping(redundant_entry)
	dirty = True

# Step 2, refetch mappings and perform sync

if dirty:
	# ctfd is really garbage...
	import time
	time.sleep(3)
	mappings = get_mappings(git_challenge_dir)
	
challenge.map_ctms(mappings)

for task_id, challtask in enumerate(challenge.challenge_tasks, 1):
	ctm = challtask.task_ctm
	
	indented_chall_desc = "\r\n".join(["> " + sl for sl in challenge.challenge_description.splitlines()])
	combined_description = f"{indented_chall_desc}    \r\n    \r\n{challtask.task_description}"
	
	update_json = {
		"category": challenge.challenge_name,
		"name": challtask.task_name,
		"value": str(challtask.task_points),
		"initial": str(challtask.task_points),
		"minimum": str(challtask.task_points),
		"decay": "0",
		"max_attempts": str(challtask.task_maxattempts),
		"description": combined_description,
		"state": "visible"
	}
	
	if task_id == 1:
		if challenge.challenge_backend == 'none':
			update_json['type'] = 'dynamic'
			update_json['function'] = 'linear'
		elif challenge.challenge_backend == 'infra':
			update_json['type'] = 'container'
			update_json['challenge_type'] = 'other'
		elif challenge.challenge_backend == 'web':
			update_json['type'] = 'container'
			update_json['challenge_type'] = 'web'
			
		if challenge.compose_file:
			update_json['compose'] = challenge.compose_file
	else:
		update_json['type'] = 'dynamic'
		update_json['function'] = 'linear'

		notice = ""
		
		if challenge.challenge_backend in ['infra','web']:
			notice += "backend systems"
		
		if len(challenge.challenge_files) > 0:
			if len(notice) > 0:
				notice += " and "
			notice += "files"
		
		if len(notice) > 0:
			update_json['description'] += f'    \r\n    \r\n*Note: {notice} for this challenge can be found in the first task.*'

	# add author information at the end
	update_json['description'] += f'    \r\n    \r\n<small>Challenge author: {challenge.challenge_author}</small>'

	print()
	print(f"[**] Syncing challenge data: {ctm.git_challenge_dir} task #{ctm.task_id}")
	req = ctfdapi.patch(f"challenges/{ctm.ctfd_challenge_id}", json=update_json)
	print(f"  Chall -> Success" if req.ok else "  Chall -> FAIL")
	
	## FLAG UPDATE LOGIC
	
	req = ctfdapi.get(f"challenges/{ctm.ctfd_challenge_id}/flags")
	assert req.ok
	
	flag_data = req.json()['data']
	assert len(flag_data) <= 1, "more than one flag detected; fix manually please"
	
	mismatch = False
	
	if len(flag_data) == 0:
		print("  Flag -> Create new one")
		req = ctfdapi.post(f"flags", json={
			"challenge": ctm.ctfd_challenge_id, 
			"content": str(challtask.task_flag),
			"data": "case_insensitive",
			"type": "regex" if challtask.task_flag_isregex else "static"
		})
		assert req.ok

	else: 
		flag_data = flag_data[0]
	
		if flag_data['type'] == 'static' and not challtask.task_flag_isregex:
			pass
		elif flag_data['type'] == 'regex' and challtask.task_flag_isregex:
			pass
		else:
			mismatch = True
		
		if flag_data['data'] != 'case_insensitive':
			mismatch = True
		
		if flag_data['content'] != challtask.task_flag:
			mismatch = True

		if mismatch:
			ctfdapi.patch(f"flags/{flag_data['id']}", json={
				"content": str(challtask.task_flag),
				"data": "case_insensitive",
				"type": "regex" if challtask.task_flag_isregex else "static",
				"id": flag_data['id']
			})
			print(f"  Flag -> Update OK" if req.ok else "  Chall -> Update fail")
		else:
			print("  Flag -> OK (no action)")
	
	## TAG UPDATE LOGIC
	
	req = ctfdapi.get(f"challenges/{ctm.ctfd_challenge_id}/tags")
	assert req.ok
	
	tags_data = req.json()['data']
	tag_entries = []
	
	for tag in tags_data:
		if (tag['value'] in tag_entries) or (tag['value'] not in challtask.task_tags):
			ctfdapi.delete(f"tags/{tag['id']}")
			continue
		tag_entries.append(tag['value'])
	
	for tag in challtask.task_tags:
		if tag not in tag_entries:
			ctfdapi.post("tags", json={"challenge": ctm.ctfd_challenge_id, "value": tag})
	
	
	print("  Tags -> Synced")
	
	# FILE UPDATE LOGIC
	
	if task_id != 1:
		continue
	
	req = ctfdapi.get(f"challenges/{ctm.ctfd_challenge_id}/files")
	assert req.ok
	
	files_data = req.json()['data']
	file_id_mapping = {}
	file_entries = {}
	file_location_entries = {}
	
	for fil in files_data:
		file_id_mapping[fil['location']] = fil['id']
	
	chall_topics = ctfdapi.get(f"challenges/{ctm.ctfd_challenge_id}/topics").json()
	challenge_file_dict = {f.name:f for f in challenge.challenge_files}

	for topic_data in chall_topics["data"]:
		ftm = FileTopicMapping.from_chall_topic_data(topic_data)
		
		if ftm:
			if ftm.file_name in file_entries: 								# duplicate
				ctfdapi.delete(f"topics/{ftm.topic_id}")
				continue
			
			if 	((ftm.file_name not in challenge_file_dict) or 						# file removed from challenge or hash mismatch, remove mapping + file
				(ftm.file_hash != file_md5hash(challenge_file_dict[ftm.file_name]))): 	 
				
				print(f"  Files -> Marking stale ({ftm.file_name})")
				ctfdapi.delete(f"topics/{ftm.topic_id}")
				continue
				
			file_entries[ftm.file_name] = ftm
			file_location_entries[ftm.location] = ftm
			
	for fil in files_data: 												# removing files for which no mapping exists
		if fil['location'] not in file_location_entries:
			print(f"  Files -> Removed stale entry ({fil['location']})")
			ctfdapi.delete(f"files/{fil['id']}")
		
	for chf in challenge.challenge_files:
		if chf.name not in file_entries:
			req = ctfdapi.post("files", data={"challenge": ctm.ctfd_challenge_id, "type": "challenge"}, files=[("file", chf.open('rb'))])
			assert req.ok
			
			newfile_data = req.json()['data'][0]
			ftm = FileTopicMapping(newfile_data['location'], file_md5hash(chf))
			req = ctfdapi.post("topics", json={"challenge": ctm.ctfd_challenge_id, "type": "challenge", "value": str(ftm)})
			assert req.ok
			
			print(f"  Files -> Created or updated ({chf.name})")
			
