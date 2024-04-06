# FauxNTP

```
usage: fauxNTP.py [-h] [--host HOST] [--port PORT] [--set UNIX_TS | --offset OFFSET] [--stop]

options:
  -h, --help       show this help message and exit
  --host HOST
  --port PORT
  --set UNIX_TS    Start with the clock set to UNIX_TS
  --offset OFFSET  Offset the clock by OFFSET seconds
  --stop           Start with the clock stopped
```

```
$ ./fauxNTP.py
FauxNTP running on :: port 123
Clock: ▶️  2024-04-06 04:54:05.244594+00:00

Available commands:
    clock.stop()                           freeze time served to clients
    clock.run()                            resume clock
    clock.set(unix_timestamp_or_datetime)  set time served to clients
    clock.setOffset(seconds)               offset time served to clients from real time
    clock.getTime()                        get unix timestamp served to clients

>>> 
```
