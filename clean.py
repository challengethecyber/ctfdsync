from ctfdsync.models import *
from ctfdsync.functions import *
from ctfdsync.ctfdapi import CtfdApi

ctfdapi = CtfdApi()

mappings = get_mappings()

for ctm in mappings:
	req = ctfdapi.get(f"challenges/{ctm.ctfd_challenge_id}")
	if not req.ok:
		print(f"Found inexistent challenge for CTM entry, removing {str(ctm)}.")
		ctfdapi.delete(f"topics/{ctm.topic_id}")
	
