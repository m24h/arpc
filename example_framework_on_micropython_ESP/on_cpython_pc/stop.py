import arpc
import asyncio
import conf

async def cmds():
	async with await arpc.connect(conf.server['host'], conf.server['port'], password=conf.server['password']) as sess:
		await sess.exec('''
import uasyncio as asyncio
asyncio.get_event_loop().stop()
print('RPC event loop is stopped')
''', __arpc_toss=True)

if __name__=='__main__':
	asyncio.run(cmds())