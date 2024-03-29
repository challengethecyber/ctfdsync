from ctfdsync.ctfdapi import CtfdApi
from ctfdsync.models import *
from pathlib import Path

ctfdapi = CtfdApi()

def get_global_config(pathhint: Path):
	testpath: Path = pathhint.resolve()
	assert testpath.is_dir()

	found_config = None
	for p in [testpath, testpath.parent, testpath.parent.parent]:
		if (p / "ctfdsync.yaml").exists():
			found_config = p / "ctfdsync.yaml"

	assert found_config
	return CtfdSyncConfig.from_yaml(found_config)

def create_placeholder_challenge():
	new_challenge = {
		"category": "",
		"description": "",
		"name": "*PLACEHOLDER*",
		"state": "hidden",
		"type": "container",
		"compose": "",
		"challenge_type": "other",
		"initial": "0",
		"minimum": "1",
		"decay": "1",
		"value": "0"
	}

	req = ctfdapi.post("challenges", json=new_challenge)
	assert req.ok

	# returns challenge id	
	return req.json()['data']['id']

def get_mappings(git_challenge_dir=None):
	mappings = []
	
	for topic_data in ctfdapi.get("topics").json()["data"]:
		ctm = ChallengeTopicMapping.from_global_topic_data(topic_data)

		# no further sanity checks here, assuming sane
		if ctm:
			# if challenge_dir_name not set, return all mappings
			if git_challenge_dir is None or ctm.git_challenge_dir == git_challenge_dir:
				mappings.append(ctm)
			
	return mappings
	
def create_challenge_for_task(git_challenge_dir, task_id):
	ctfd_challenge_id = create_placeholder_challenge()
	create_gitdir_mapping(ctfd_challenge_id, git_challenge_dir, task_id)
	
def delete_challenge_with_mapping(ctm):
	ctfdapi.delete(f"challenges/{ctm.ctfd_challenge_id}")
	ctfdapi.delete(f"topics/{ctm.topic_id}")

def create_gitdir_mapping(ctfd_challenge_id, git_challenge_dir, task_id):

	print(f"(-- MAPPER --) {ctfd_challenge_id} - {git_challenge_dir} - {task_id}")
	
	## GLOBAL CTM DISCOVERY
	
	mappings = get_mappings()
	mappings_dict = {}

	for ctm in mappings:
		if mappings_dict.get(ctm.ctfd_challenge_id):
			# print("Duplicate topic for challenge detected. Queueing removal of this one.")
			ctm.pending_action = TopicMappingAction.REMOVE
			continue
	
		mappings_dict[ctm.ctfd_challenge_id] = ctm
		
		mismatch = False
		
		if ctm.git_challenge_dir == git_challenge_dir:
			if ctm.task_id == task_id:
				if ctm.ctfd_challenge_id != ctfd_challenge_id:
					mismatch = True
					ctm.pending_action = TopicMappingAction.REMOVE

		if ctm.ctfd_challenge_id == ctfd_challenge_id:
		
			if ctm.git_challenge_dir != git_challenge_dir:
				mismatch = True
				ctm.pending_action = TopicMappingAction.REMOVE
				
			if ctm.task_id != task_id:
				mismatch = True
				ctm.pending_action = TopicMappingAction.REMOVE
			
		if mismatch:
			# print("Mismatch in current mapping: queueing removal and readd.")
			
			new_ctm = ChallengeTopicMapping(ctfd_challenge_id, git_challenge_dir, task_id)
			new_ctm.pending_action = TopicMappingAction.ADD
			mappings.append(new_ctm)
			
		else:
			# print("Found a matching global mapping: challenge already mapped in CTFd portal")	
			pass 

	
	
	mappings_by_action = sorted(mappings, key=lambda x: x.pending_action.value, reverse=True)

	## GLOBAL CTM ACTIONS

	for ctm in mappings_by_action:
		if ctm.pending_action == TopicMappingAction.REMOVE:
			# print(f"Removing CTM with topic id {ctm.topic_id}")
			req = ctfdapi.delete(f"topics/{ctm.topic_id}")
				
			print(f"  CTM (gdel) -> Success" if req.ok else "  CTM (gdel) -> FAIL")
		if ctm.pending_action == TopicMappingAction.ADD:
			# print(f"Adding new CTM")
			req = ctfdapi.post("topics", json={"challenge": ctm.ctfd_challenge_id, "type": "challenge", "value": str(ctm)})
			print(f"  CTM (gadd) -> Success" if req.ok else "  CTM (gadd) -> FAIL")
				

	## CHALL CTM DISCOVERY

	chall_topics = ctfdapi.get(f"challenges/{ctfd_challenge_id}/topics").json()

	mappings = []

	for topic_data in chall_topics["data"]:
		ctm = ChallengeTopicMapping.from_chall_topic_data(topic_data)
		
		if ctm:
			mappings.append(ctm)
			if len(mappings) > 1:
				# print("Found more than one mapping for challenge. Removing this one.")
				ctm.pending_action = TopicMappingAction.REMOVE
				continue
		
			if ctm.ctfd_challenge_id == ctfd_challenge_id and ctm.git_challenge_dir == git_challenge_dir and ctm.task_id == task_id:
				# print("Found a matching chall mapping: challenge already mapped in CTFd portal")
				pass
			else:
				# print("Erroneous mapping present for challenge. Removing.")
				ctm.pending_action = TopicMappingAction.REMOVE
			
	## CHALL CTM ACTIONS

	if len(mappings) == 0:
		# print("Chall-level mapping missing. Adding it now.")
		new_ctm = ChallengeTopicMapping(ctfd_challenge_id, git_challenge_dir, task_id)
		new_ctm.pending_action = TopicMappingAction.ADD
		mappings.append(new_ctm)

	mappings_by_action = sorted(mappings, key=lambda x: x.pending_action.value, reverse=True)

	for ctm in mappings_by_action:
		if ctm.pending_action == TopicMappingAction.REMOVE:
			req = ctfdapi.delete(f"topics?type=challenge&target_id={ctm.target_id}")
			print(f"  CTM (cdel) -> Success" if req.ok else "  CTM (cdel) -> FAIL")
			
		if ctm.pending_action == TopicMappingAction.ADD:
			# print(f"Adding new CTM")
			req = ctfdapi.post("topics", json={"challenge": ctm.ctfd_challenge_id, "type": "challenge", "value": str(ctm)})
			print(f"  CTM (cadd) -> Success" if req.ok else "  CTM (cadd) -> FAIL")
	

import hashlib

def file_md5hash(pathfile, hash_factory=hashlib.md5, chunk_num_blocks=128):
    h = hash_factory()
    with pathfile.open('rb') as f: 
        while chunk := f.read(chunk_num_blocks*h.block_size): 
            h.update(chunk)
    return h.hexdigest()
