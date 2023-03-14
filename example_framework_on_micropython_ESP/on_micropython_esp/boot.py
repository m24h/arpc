# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import gc
import network
import time
import conf
import sys

import micropython
micropython.alloc_emergency_exception_buf(100)

#init board
try:
	import init
except BaseException as e:
	sys.print_exception(e)
gc.collect()

#init wlan AP
wlan = network.WLAN(network.AP_IF) # create access-point interface
if conf.ap is None or not conf.ap['active']:
		wlan.active(False)
else:
		wlan.active(True)
		if conf.ap['password']=='':
			wlan.config(essid=conf.ap['ssid'], authmode=network.AUTH_OPEN)
		else:
			wlan.config(essid=conf.ap['ssid'], authmode=network.AUTH_WPA_WPA2_PSK, password=conf.ap['password'])
		wlan.ifconfig((conf.ap['ip'], conf.sta['mask'], conf.ap['ip'], conf.ap['ip']))
		print ('AP config: SSID=', conf.ap['ssid'], ' IF=',wlan.ifconfig(), sep='');
gc.collect()

#init wlan STA
wlan = network.WLAN(network.STA_IF) # create station interface
if conf.sta is None or not conf.sta['active']:
		wlan.active(False)
else:
		wlan.active(True)       # activate the interface
		if conf.sta['ip']!='' and conf.sta['ip']!='0.0.0.0':
			wlan.ifconfig((conf.sta['ip'], conf.sta['mask'], conf.sta['gw'], conf.sta['dns']))
		else:
			wlan.ifconfig('dhcp')
		wlan.connect(conf.sta['ssid'], conf.sta['password'])
		while not wlan.isconnected():
			time.sleep(0.5)
		print ('STA config: SSID=', conf.sta['ssid'], ' IF=',wlan.ifconfig(), sep='');
gc.collect()

# start RPC server
if conf.rpc is not None and conf.rpc['active']:
	import arpc
	import uasyncio as asyncio
	rpc=arpc.RPC()
	
	#some useful command
	rpc['list']=lambda : tuple(rpc.keys())
	rpc['eval']=eval
	rpc['exec']=exec
	rpc['gcc']=gc.collect

	#scheduled and delayed exec
	@rpc('todo')
	def todo(tout, exe):
		async def _todo():
			await asyncio.sleep(tout)
			exec(exe)
		asyncio.get_event_loop().create_task(_todo())
	
	# other RPC commands
	try:
		import rpcs
	except BaseException as e:
		sys.print_exception(e)
	gc.collect()
		
	try:
		import _thread
		_thread.stack_size(8192)
		def rpc_run():
			asyncio.get_event_loop().run_until_complete(arpc.server(rpc, port=conf.rpc['port'], password=conf.rpc['password']))
			gc.collect()
			asyncio.get_event_loop().run_forever()
		_thread.start_new_thread(rpc_run, ())
		print ('RPC started at', conf.rpc['port'], 'in thread mode')
	except ImportError: #no thread support in ESP8266
		asyncio.get_event_loop().run_until_complete(arpc.server(rpc, port=conf.rpc['port'], password=conf.rpc['password']))
		print ('RPC started at', conf.rpc['port'], 'in exclusive mode')
		gc.collect()
		asyncio.get_event_loop().run_forever() #will be blocked here, no REPL/webrepl until event loop is stopped through some RPC calling
gc.collect()

# start webrepl
if conf.webrepl is not None and conf.webrepl['active']:
	import webrepl
	webrepl.start(port=conf.webrepl['port'], password=conf.webrepl['password'])
gc.collect()