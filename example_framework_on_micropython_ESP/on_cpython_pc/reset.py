import arpc
import asyncio
import conf

async def cmds():
	async with await arpc.connect(conf.server['host'], conf.server['port'], password=conf.server['password']) as sess:
		await sess.todo(1,'''
print('Reset ...')
import machine
machine.reset()
''')

asyncio.run(cmds())