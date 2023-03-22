from __main__ import rpc

#example only, can be removed
rpc['hw_id']='ESP32.TTT.20230309'
rpc['help']='version(): return current version'

from init import version

@rpc('version')
def _version():
	return version
	
