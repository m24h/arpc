import arpc
import asyncio
import conf
from sys import argv

async def cmds():
	async with await arpc.connect(conf.server['host'], conf.server['port'], password=conf.server['password']) as sess:
		print (await eval('sess.'+argv[1]))

if __name__=='__main__':
	asyncio.run(cmds())