import enum
import re
import yaml
from pathlib import Path, PurePosixPath

class Challenge:
	def __init__(self):
		pass
		
	@classmethod
	def from_yaml(cls, yamlfile: Path):
		yamlfile = yamlfile.resolve()
		assert yamlfile.exists()
		yml = yaml.safe_load(yamlfile.open())
		
		new = cls()
	
		assert re.fullmatch(r"[a-zA-Z0-9 \-]+", yml['challenge_name'])
		new.challenge_name = yml['challenge_name']
		
		assert re.fullmatch(r".+", yml['challenge_author'])
		new.challenge_author = yml['challenge_author']
		
		assert isinstance(yml['challenge_description'], str)
		new.challenge_description = yml['challenge_description']
		
		assert type(yml['challenge_tasks']) == list and len(yml['challenge_tasks']) >= 1

		if "challenge_files" not in yml: 
			yml["challenge_files"] = []
		assert type(yml['challenge_files']) == list
		
		new.challenge_files = []
		
		for f in yml['challenge_files']:
			assert type(f) == str
			chall_file = Path(yamlfile.parent) / f
			assert chall_file.exists(), f"File '{chall_file}' does not exist."
			assert re.fullmatch(r"[a-zA-Z0-9\-_\.]+", chall_file.name), "Disallowed characters in file name [a-zA-Z0-9\-_\.]+"
			new.challenge_files.append(chall_file)

		if "challenge_backend" not in yml: 
			yml["challenge_backend"] = 'none'
			
		assert yml["challenge_backend"] in ['none', 'web', 'infra']

		
		if yml["challenge_backend"] in ['web', 'infra']:
			compose_file = Path(yamlfile.parent) / "docker-compose.yaml"
			assert compose_file.exists()
			new.compose_file = compose_file.read_text()
		else:
			new.compose_file = None
		
		new.challenge_backend = yml['challenge_backend']
		
		assert "challenge_tasks" in yml and len(yml['challenge_tasks']) > 0

		new.challenge_tasks = []
		for task in yml['challenge_tasks']:
			ct = ChallengeTask.from_yaml_object(task)
			new.challenge_tasks.append(ct)
			
		return new
		
	def map_ctms(self, ctms):
		assert len(ctms) == len(self.challenge_tasks), "Amount of tasks needs the same amount of CTMs - you may need to create additional ones. Or manually remove redundant ones."
		
		for task_id in range(1, len(self.challenge_tasks)+1):
			task_ctm = list(filter(lambda c: c.task_id == task_id, ctms))
			assert len(task_ctm) == 1
			task_ctm = task_ctm[0]
			
			self.challenge_tasks[task_id-1].task_ctm = task_ctm
	
class ChallengeTask:
	def __init__(self):
		pass
	
	@classmethod
	def from_yaml_object(cls, obj):
		new = cls()
	
		assert re.fullmatch(r"[a-zA-Z0-9\-]+", obj['task_name'])
		new.task_name = obj['task_name']
		
		assert isinstance(obj['task_description'], str)
		new.task_description = obj['task_description']
		
		assert type(obj['task_flag']) in [str, int]
		assert re.fullmatch(r".+", str(obj['task_flag']))
		new.task_flag = str(obj['task_flag'])
		
		assert type(obj['task_flag_isregex']) == bool
		new.task_flag_isregex = obj['task_flag_isregex']
		
		assert type(obj['task_points']) == int and obj['task_points'] > 0
		new.task_points = obj['task_points']
		
		assert type(obj['task_tags']) == list
		assert all([type(i) == str for i in obj['task_tags']])
		new.task_tags = obj['task_tags']
		
		assert type(obj['task_maxattempts']) == int and obj['task_maxattempts'] >= 0
		new.task_maxattempts = obj['task_maxattempts']
		
		assert obj['task_difficulty'] in ['beginner', 'easy', 'medium', 'hard']
		new.task_difficulty = obj['task_difficulty']
		
		return new

class TopicMappingAction(enum.Flag):
	NONE = enum.auto()
	ADD = enum.auto()
	REMOVE = enum.auto()

class ChallengeTopicMapping:
	def __init__(self, ctfd_challenge_id, git_challenge_dir, task_id, topic_id=None, target_id=None):
		self.topic_id = topic_id
		self.ctfd_challenge_id = ctfd_challenge_id
		self.git_challenge_dir = git_challenge_dir
		self.task_id = task_id
		self.pending_action = TopicMappingAction.NONE
		self.target_id = target_id

	@classmethod
	def from_global_topic_data(cls, topic_data):
		topic = topic_data["value"]
		topic_id = int(topic_data["id"])
		return cls.from_topic_id_and_value(topic, topic_id)
	    		
	@classmethod
	def from_chall_topic_data(cls, topic_data):
		topic = topic_data["value"]
		topic_id = int(topic_data["topic_id"])
		target_id = int(topic_data["id"])
		return cls.from_topic_id_and_value(topic, topic_id, target_id=target_id)
	
	@classmethod
	def from_topic_id_and_value(cls, topic, topic_id, target_id=None):
		if topic.startswith("link#") and topic.count("#") == 4:
			ctfd_challenge_id, git_challenge_dir, task_id = topic.rstrip("#").split("#")[1:]
			return cls(int(ctfd_challenge_id), git_challenge_dir, int(task_id), topic_id, target_id=target_id)
		else:
	    		return False
	    		
	def __bool__(self):
		return True
		
	def __str__(self):
		return f"link#{self.ctfd_challenge_id}#{self.git_challenge_dir}#{self.task_id}#"
		

class FileTopicMapping:
	def __init__(self, location, file_hash, topic_id=None, target_id=None):
		self.location = location
		self.file_hash = file_hash
		self.topic_id = topic_id
		self.target_id = target_id
		self.pending_action = TopicMappingAction.NONE
		
	@classmethod
	def from_chall_topic_data(cls, topic_data):
		topic = topic_data["value"]
		topic_id = int(topic_data["topic_id"])
		target_id = int(topic_data["id"])
		return cls.from_topic_id_and_value(topic, topic_id, target_id=target_id)
		
	@classmethod
	def from_topic_id_and_value(cls, topic, topic_id, target_id=None):
		if topic.startswith("file#") and topic.count("#") == 3:
			location, file_hash = topic.rstrip("#").split("#")[1:]
			return cls(location, file_hash, topic_id, target_id=target_id)
		else:
	    		return False
	
	@property
	def file_name(self):
		return PurePosixPath(self.location).name
	
	def __bool__(self):
		return True
		
	def __str__(self):
		return f"file#{self.location}#{self.file_hash}#"
