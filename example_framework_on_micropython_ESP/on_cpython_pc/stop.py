import arpc
import asyncio
import conf

async def cmds():
	async with await arpc.connect(conf.server['host'], conf.server['port'], password=conf.server['password']) as sess:
		try:
			await sess.todo(1,'''
import uasyncio as asyncio
asyncio.get_event_loop().stop()
print('RPC event loop is stopped')
''')
		except: #no .todo() RPC command, try .exec() command
			try:
				await asyncio.wait_for(sess.exec('''
import uasyncio as asyncio
asyncio.get_event_loop().stop()
print('RPC event loop is stopped')
'''), 1)
			except:
				pass

asyncio.run(cmds())