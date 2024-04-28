#!/usr/bin/env python3
import dataclasses as dc
import struct, socketserver, socket, time, argparse, code, threading
from datetime import datetime, UTC

@dc.dataclass
class NTPTimestamp:
    bytes: bytes = b"\x00\x00\x00\x00\x00\x00\x00\x00"

    def to_datetime(self):
        sec = int.from_bytes(self.bytes) / 2**32
        return datetime.fromtimestamp(sec - 2208988800, UTC)

    @classmethod
    def from_datetime(cls, dt):
        if dt.tzinfo is not UTC:
            raise ValueError("datetime must be in UTC")
        return cls.from_unix(dt.timestamp())

    @classmethod
    def from_unix(cls, ts):
        ts += 2208988800 # align 1970 epoch to 1900 epoch
        ts %= 2**32 # cap seconds to 32 bits
        return cls(int(ts * 2**32).to_bytes(8))

@dc.dataclass
class NTPPacket:
    ref_time: NTPTimestamp
    origin_time: NTPTimestamp
    rx_time: NTPTimestamp
    tx_time: NTPTimestamp
    stratum: int = 1
    refid: bytes = b"FAUX"

    def to_bytes(self):
        return struct.pack("!BBbbii4s8s8s8s8s",
            0x1c, # no leap, v3, server
            self.stratum,
            0, # polling interval 1s
            -20, # precision 0.0009ms
            0, # root delay 0s
            5, # root dispersion 0.07ms,
            self.refid,
            self.ref_time.bytes,
            self.origin_time.bytes,
            self.rx_time.bytes,
            self.tx_time.bytes
        )

    @classmethod
    def from_bytes(cls, data):
        data = struct.unpack("!BBbbii4s8s8s8s8s", data)
        return cls(
            stratum=data[1],
            refid=data[6],
            ref_time=NTPTimestamp(data[7]),
            origin_time=NTPTimestamp(data[8]),
            rx_time=NTPTimestamp(data[9]),
            tx_time=NTPTimestamp(data[10])
        )


class IP6UDPServer(socketserver.UDPServer):
    address_family = socket.AF_INET6

class FauxNTPHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        req = NTPPacket.from_bytes(self.rfile.read())

        outTime = NTPTimestamp.from_unix(clock.getTime())
        self.wfile.write(
            NTPPacket(
                ref_time=outTime,
                origin_time=req.tx_time,
                rx_time=outTime,
                tx_time=outTime
            ).to_bytes()
        )


@dc.dataclass
class Clock:
    offset: float = 0.
    stopped_at: float = None
    _silent = True

    def stop(self):
        self.stopped_at = time.time()

        self._silent or print(self.getStatus())

    def run(self):
        self.stopped_at = None

        self._silent or print(self.getStatus())

    def set(self, dt):
        if isinstance(dt, datetime):
            dt = dt.timestamp()

        self.offset = dt - (self.stopped_at or time.time())

        self._silent or print(self.getStatus())

    def setOffset(self, offset):
        self.offset = offset

        self._silent or print(self.getStatus())

    def getTime(self):
        return (self.stopped_at or time.time()) + self.offset

    def getStatus(self):
        return f'{"⏸️" if self.stopped_at else "▶️"}  {datetime.fromtimestamp(self.getTime(), UTC)}'


clock = Clock()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="::")
    parser.add_argument("--port", default=123, type=int)
    setters = parser.add_mutually_exclusive_group()
    setters.add_argument("--set", metavar="UNIX_TS", type=float, help="Start with the clock set to UNIX_TS")
    setters.add_argument("--offset", type=float, help="Offset the clock by OFFSET seconds")
    parser.add_argument("--stop", action="store_true", help="Start with the clock stopped")
    args = parser.parse_args()

    if args.stop:
        clock.stop()
    if args.set:
        clock.set(args.set)
    if args.offset:
        clock.setOffset(args.offset)

    clock._silent = False

    server = IP6UDPServer((args.host, args.port), FauxNTPHandler)
    threading.Thread(target=server.serve_forever).start()

    code.interact(
        banner=
f"""FauxNTP running on {args.host} port {args.port}
Clock: {clock.getStatus()}

Available commands:
    clock.stop()                           freeze time served to clients
    clock.run()                            resume clock
    clock.set(unix_timestamp_or_datetime)  set time served to clients
    clock.setOffset(seconds)               offset time served to clients from real time
    clock.getTime()                        get unix timestamp served to clients
""",
        local={"clock": clock},
        exitmsg="Stopping..."
    )

    server.shutdown()

if __name__ == "__main__":
    main()
