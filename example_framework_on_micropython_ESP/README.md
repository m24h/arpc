# About this framework
A framework sets up RPC server in the micropython environment on a ESP32/ESP8266 board, with RPC methods: 'exec', 'eval', etc.
Using this framework, program running in CPython on PC end can do many things without downloading any codes to board's flash.

Useful WIFI AP/STA, WebREPL are also provided in this framework.

See the codes for details.

# About compatibility of json module:

Some incompatibilities were found between CPython/Micropython json module, so don't transmit objects other than number, string, boolean, None, list and dict.
Incompatible expressions are discarded and cause the caller to wait for a response that will not come.

# User scripts

init.py is used for user to initialize something related to some type of board before framework working.

rpcs.py is used for user to set up customized RPC methods.

# About ESP8266

ESP8266 has no thread mode, so the routine will be blocked at RPC event loop, and REPL/WebREPL/main.py will be never reachable. 
But a stop.py scripts is provided, to stop the RPC event loop, then REPL/WebREPL are available for updating flash and etc.
stop.py depends on 'exec' 'todo' RPC methods defined in boot.py, if there's no any mechanism to stop the event loop,
maybe re-burning micropython firmware can help it out.

Micropython on ESP8266 does not provide '__name__' attribute for function, so the PRC name must be explicitly provided when decorating a function as RPC command.

