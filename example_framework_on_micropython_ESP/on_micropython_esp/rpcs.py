from __main__ import rpc

#example only, can be removed

from init import version

@rpc('version')
def _version():
	return version