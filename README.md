# arpc
Tiny Pure Python Bi-Direction RPC Module, Compatible with MicroPython

## Features:

* Small, single file
* Pure Python
* Need no 3-party libraries, use only standard libraries
* Bidirectional RPC calling between Client and Server
* Parallel in asynchronous mode
* Have single password authentication
* Compatible with Micropython
* Disconnect detection using heart-beat (timeout configurable)
* Decorator-modify-Command mode and local-method-like calling mode
* Support simple dumpable object, normal function, coroutine function
* Exception remote-catching and local-rising
* Stream-like not-wait-result calling in simple way, just add a '__arpc_toss=True'  keyword argument

## Install
```bash
mpremote mip install github:m24h/arpc
```

## Server style
```python
import arpc
import asyncio
rpc=arpc.RPC()
@rpc()
def func(a, b=None):
  pass

asyncio.get_event_loop().run_until_complete(arpc.server(rpc, port=8267, password=None, hbeat=30))
asyncio.get_event_loop().run_forever()
```
## Client style
```python
import arpc
import asyncio
rpc=arpc.RPC()
@rpc('name')
def client_func(a, b=None):
  pass
  
async def client():
  async with await arpc.connect('127.0.0.1', rpc=rpc, password='rrr') as remote:
    remote.func(3,4)
asyncio.run(client())
```
  
## More examples  

See my <https://github.com/m24h/ESP8266ADDA>

## More detail

See the source file


