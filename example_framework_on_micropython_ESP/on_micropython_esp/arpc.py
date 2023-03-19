# Copyright 2023 m24h, see http://www.apache.org/licenses/LICENSE-2.0
# usage and examples: at the tail
try:
	import asyncio
except ImportError:
	import uasyncio as asyncio

import json

_sessions={}

# a class for RPC name mapping
class RPC(dict):
	#decorator to specify a function as RPC command
	def __call__(self, name=None):
		def decorator(func):
			self[name or func.__name__]=func
			return func
		return decorator

#the exception of remote calling, .cls is remote exception class name, .args are remote exception args
class RemoteException(Exception):
	def __init__(self, cls, *args):
		self.cls=cls
		super().__init__(*args)

#a RPC connection session, a context object, don't forget to close() it after use
class Session(object):
	def __init__(self, rpc, reader, writer):
		self._task=None #dispatcher task, None means session is closed
		self._hbtask=None #heat beat task
		self._rpc=rpc
		self._reader=reader 
		self._writer=writer
		self._reqs=dict() #waiting calling requests
		self._wlock=asyncio.Lock()
	
	async def __aenter__(self):
		return self
	
	async def __aexit__(self, type, value, trace):
		if self._task is not None:
			if self._task is not asyncio.current_task():  
				self._task.cancel()
				await self._task
			self._task=None
		if self._hbtask is not None:
			self._hbtask.cancel()
			await self._hbtask
		if self._writer is not None: 
			try: #maybe already closed if disconnected
				self._writer.close()
				await self._writer.wait_closed()
			except:
				pass
			self._writer=None
		self._reader=None #only writer is closeable in CPython
	
	async def _write(self, obj):
		data=json.dumps(obj, separators=(',', ':')).encode('ISO8859-1')
		if (w:=self._writer): #maybe closed
			async with self._wlock:
				w.write(data+b'\r\n')
				await w.drain()
	
	async def _read(self):
		while (r:=self._reader): #maybe closed
			data=await r.readline()
			#print('r:', data)
			if not data:  #EOF, disconnected
				raise OSError('connection is closed')
			try:
				data=json.loads(data.decode('ISO8859-1'))	#something wrong for utf-8 between micropython and cpython	
				if isinstance(data, dict): 
					return data
			except ValueError:  #bad json string, ignore and continue
				pass
	
	#it return a coroutine from __call__(), if name conflicts with internal attributes, use __call__ instead
	def __getattr__(self, name):
		return lambda *args, **kargs : self(name, *args, **kargs)
	
	async def __call__(self, name, *args, **kargs):
		if self._task is None:
			raise RuntimeError('session is closed')
		evt=asyncio.Event()
		rid=id(evt)
		try:
			self._reqs[rid]=evt
			await self._write({'act':'cmd', 'rid':rid, 'name':name, 'args':args, 'kargs':kargs})
			await evt.wait()
			resp=self._reqs[rid]
		finally:
			del self._reqs[rid]
		if isinstance(resp, BaseException): #exception from dispatcher
			raise resp
		else:
			return resp
	
	async def _heartbeat(self, timeout):
		try:
			while self._task is not None: 
				await self._write({'act':'hb'})
				await asyncio.sleep(timeout)
		except (asyncio.CancelledError, OSError):
			pass		 
	
	#schedule a new-created task for awaitable RPC function, in which RPC callback is possible
	async def _schedule(self, rid, coro):
		try:
			tid=id(asyncio.current_task())
			_sessions[tid]=self
			res=await coro
		except BaseException as e:
			try:
				await self._write({'act':'err', 'rid':rid, 'cls':type(e).__name__, 'args':e.args})
			except:
				pass
		else:
			await self._write({'act':'res', 'rid':rid, 'res':res})
		finally:
			del _sessions[tid]					
		
	#dispatcher for RPC calling
	async def _dispatch(self):
		try:
			exc=None
			while self._task is not None: #maybe closed
				data=await self._read()
				act=data.get('act',None)
				rid=data.get('rid',None)
				if act=='cmd':
					if not self._rpc or (name:=data.get('name', None)) not in self._rpc:
						await self._write({'act':'err', 'rid':rid, 'cls':'NameError', 'args':('No such command',)})
					elif callable(cmd:=self._rpc[name]): 
						try:
							#cmd must return as soon as possible, don't make another RPC request directly, or dispatcher will be dead-locked
							res=cmd(*data.get('args',()), **data.get('kargs',{}))
							if hasattr(res, 'send') and callable(res.send): #a coroutine
								#create a new task to handle the coroutine (it will most likely take some time)
								asyncio.get_event_loop().create_task(self._schedule(rid, res))
							else:
								await self._write({'act':'res', 'rid':rid, 'res':res})
						except BaseException as e:
							await self._write({'act':'err', 'rid':rid, 'cls':type(e).__name__, 'args':e.args})
					else: #must be a dumpable object
						await self._write({'act':'res', 'rid':rid, 'res':cmd})					
				elif act=='res':
					if (evt:=self._reqs.get(rid, None)):
						self._reqs[rid]=data.get('res',None)
						evt.set()
				elif act=='err':
					if (evt:=self._reqs.get(rid, None)):
						self._reqs[rid]=RemoteException(data.get('cls',None), data.get('args',()))
						evt.set()
				else: #unknown
					pass
		except asyncio.CancelledError: #cancelled by another task
			pass
		except OSError as e:
			exc=e
		finally:
			self._task=None
			exc=exc or RuntimeError('session is closed')
			for k in self._reqs:
				evt=self._reqs[k]
				if isinstance(evt, asyncio.Event):
					self._reqs[k]=exc
					evt.set()

#connect to a server, return the Session object
async def connect(host, port=8267, rpc=None, password=None, hbeat=30):
		r,w=await asyncio.open_connection(host, port)
		sess=Session(rpc, r, w)
		if password:
			await sess._write({'act':'login', 'password':password})
		if hbeat:
			sess._hbtask=asyncio.get_event_loop().create_task(sess._heartbeat(hbeat))
		sess._task=asyncio.get_event_loop().create_task(sess._dispatch())
		return sess

#start a server listening, return an asyncio.Server object
async def server(rpc, host='0.0.0.0', port=8267, password=None, hbeat=30):
	async def dispatcher(r, w):
		async with Session(rpc, r, w) as sess:
			try:
				if password:
					data=await sess._read()
					if data.get('act',None)!='login' or data.get('password',None)!=password:
						return #do not answer anything, just leave, connection will be closed
				sess._task=asyncio.current_task()
				if hbeat:
					sess._hbtask=asyncio.get_event_loop().create_task(sess._heartbeat(hbeat))
				await sess._dispatch()
			except OSError: # ignore client disconnect
				pass
	return await asyncio.start_server(dispatcher, host, port)

#close a session
async def close(sess):
	await sess.__aexit__(None,None,None)
	
#check if session is closed
def is_closed(sess):
	return sess._task is None

#get current session, this should be called inside async RPC command only
def session():
	tid=id(asyncio.current_task())
	return _sessions.get(tid, None)

#test and example
if __name__=='__main__':
	import sys
	if len(sys.argv)>1 and sys.argv[1]=='s': # python arpc.py s
		#as server
		rpc=RPC()

		#data RPC, just return data
		rpc['version']={'major':1, 'minor':0}
		
		#simple RPC, in this function, calling back to client RPC is inhibited (or result in deadlock)
		#and it should return as soon as possible, coz. all simple RPC is run in dispatcher task
		@rpc() 
		def inc(u):
			return u+1
		
		#coroutine RPC, a new task will be created for it, calling back to client RPC is OK
		@rpc('dec')
		async def test(u):
			sess=session()
			await sess.prn("I can call back to client")
			await asyncio.sleep(3)
			await sess.prn("a big work (sleep) is done")
			return u-1
			
		print('server started')
		try:
			asyncio.get_event_loop().run_until_complete(server(rpc, password='rrr'))
			asyncio.get_event_loop().run_forever()
		except KeyboardInterrupt:
			pass
		print('server stopped')
			
	else: # python arpc.py c
		# as client
		rpc=RPC()
		
		@rpc()
		def prn(s):
			print("sever event: ", s)
		
		async def client():
			async with await connect('127.0.0.1', rpc=rpc, password='rrr') as sess:
				try:
					print(await sess.version())
					print(await sess.inc(5))
					print(await sess.dec(5))
				except Exception as e:
					print(e)

		asyncio.get_event_loop().run_until_complete(client())

