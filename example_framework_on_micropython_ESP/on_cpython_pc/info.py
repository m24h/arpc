import arpc
import asyncio
import conf

import binascii

async def init():
	async with await arpc.connect(conf.server['host'], conf.server['port'], password=conf.server['password']) as sess:
		await sess.exec('import sys')
		print('sys.implementation : ', await sess.eval('repr(sys.implementation)')) # now upython's json.dumps can dump sys.implementation incorrectly, but cpython's json.loads() fails to load it back
		await sess.exec('import machine')
		print('machine.freq :', await sess.eval('machine.freq()'))
		print('machine.unique_id :', binascii.hexlify((await sess.eval('machine.unique_id()')).encode('iso8859-1')).decode('iso8859-1'))
		await sess.exec('import micropython')
		print('micropython.stack_use :', await sess.eval('micropython.stack_use()'))
		
asyncio.run(init())