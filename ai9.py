"""
Copyright (c) 2021 Robert Jördens <rj@quartiq.de>

MIT License

Permission is hereby granted, free of charge, to any
person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without
limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice
shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import codecs
import logging
import asyncio
from enum import IntEnum, unique
import struct
from collections import defaultdict
import typing

import bleak

import syss_crc

logger = logging.getLogger(__name__)


crc = syss_crc.CRC()
crc.set_config_by_name("CRC-16/MODBUS")


class DateTime(typing.NamedTuple):
    _fmt = struct.Struct(">BBBBBB")
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int

    @classmethod
    def unpack(cls, buf):
        return cls._make(cls._fmt.unpack(buf))

    def pack(self):
        return self._fmt.pack(*self)


class FiberSettings(typing.NamedTuple):
    _fmt = struct.Struct(">16B")
    # 0000641e01140c14281e0100288c8200
    data: typing.List[int]

    @classmethod
    def unpack(cls, buf):
        return cls._make((cls._fmt.unpack(buf),))

    def pack(self):
        return self._fmt.pack(*self.data)


class FiberFunc(typing.NamedTuple):
    _fmt = struct.Struct(">12B")
    # 02000001010001010a0109000000
    data: typing.List[int]

    @classmethod
    def unpack(cls, buf):
        return cls._make((cls._fmt.unpack(buf),))

    def pack(self):
        return self._fmt.pack(*self.data)


class HeatSettings(typing.NamedTuple):
    _fmt = struct.Struct(">8B")
    # 04141211100f0000
    data: typing.List[int]

    @classmethod
    def unpack(cls, buf):
        return cls._make((cls._fmt.unpack(buf),))

    def pack(self):
        return self._fmt.pack(*self.data)


class AdminSettings(typing.NamedTuple):
    _fmt = struct.Struct(">12B")
    # 070507070905040412000000
    et: typing.List[int]
    zero: typing.List[int]

    @classmethod
    def unpack(cls, buf):
        d = cls._fmt.unpack(buf)
        assert d[9:12] == (0,)*3
        return cls._make((d[:9], d[9:12]))

    def pack(self):
        return self._fmt.pack(*self.et, *self.zero)


class RecordMeta(typing.NamedTuple):
    datetime: DateTime
    failure: int
    loss: int
    angles: typing.List[int]
    face_quality: int
    coordinates: typing.List[int]
    settings: FiberSettings
    face_detection: int
    angle_detection: int
    autofocus: int
    admin: AdminSettings
    charge: int
    image_len: int
    image_handle: int

    @classmethod
    def unpack(cls, buf):
        dt = DateTime.unpack(buf[:6])
        fa, lo, *angles, fq = struct.unpack(">6B", buf[6:12])
        co = struct.unpack(">12H", buf[12:36])
        se = FiberSettings.unpack(buf[36:52])
        fd, ad, af = struct.unpack(">3B", buf[52:55])
        adm = AdminSettings.unpack(buf[55:67])
        ch, img_len, img_hdl = struct.unpack(">BHB", buf[67:])
        return cls._make((dt, fa, lo, angles, fq, co, se, fd, ad, af, adm,
                          ch, img_len, img_hdl))

    def pack(self):
        return (
            self.datetime.pack() +
            struct.pack(">6B12H", self.failure, self.loss, *self.angles,
                        self.face_quality, *self.coordinates) +
            self.settings.pack() +
            struct.pack(">3B", self.face_detection, self.angle_detection,
                        self.autofocus) +
            self.admin.pack() +
            struct.pack(">BHB", self.charge, self.image_len,
                        self.image_handle))


@unique
class Op(IntEnum):
    UNKNOWN_4 = 0x00  # ? firmware
    SET_FIBER_SETTINGS = 0x10
    GET_FIBER_SETTINGS = 0x11
    SET_FIBER_FUNC = 0x12
    GET_FIBER_FUNC = 0x13
    SET_HEAT_TIME = 0x14
    GET_HEAT_TIME = 0x15
    SET_FIBER_ADMIN = 0x16
    GET_FIBER_ADMIN = 0x17
    SET_AIO = 0x19  # ? Aio1-4
    GET_AIO = 0x20  # ? Aio1-4
    SET_RECORD_READ = 0x21  # mark read
    GET_RECORD_IMG = 0x22
    GET_CURRENT_RECORD = 0x23
    GET_TOTAL_COUNT = 0x25
    UNKNOWN = 0x26  # ? 0x88
    GET_CURRENT_COUNT = 0x27  # HH: 0, number of splices
    UNKNOWN_1 = 0x32  # set 12+4 bytes
    UNKNOWN_2 = 0x33  # cmd
    UNKNOWN_3 = 0x34  # set var bytes
    GET_SERIAL = 0x35  # string
    GET_DATETIME = 0x39  # 6b YMDhms
    SET_FACTORY_MENU_CALL = 0x41  # cmd
    SET_MODE = 0x42  # normal, manual, arc cal?
    GET_MODE = 0x43
    UNKNOWN_6 = 0x44  # test firmware upgrade
    SET_CONNECTED = 0x45  # ? send connected
    GET_ASYNC = 0x48  # ? some async event response
    GET_RECORD_LAST = 0x49  # last record index
    GET_RECORD = 0x4a
    SET_RECORD_CLEAR = 0x4b  # ?
    SET_OPM_VFL_POWERDOWN = 0xa0
    SET_OPM_UNITS = 0xa1
    GET_OPM = 0xa2
    SET_VFL_MODE = 0xa3
    SET_OPM_WAVELENGTH = 0xa4
    UNKNOWN_5 = 0xa6  # query OPM/VFL?
    MOVE_MOTOR = 0xe0
    SET_ARC = 0xe1
    SET_MOTOR_RESET = 0xe2
    SET_CLEAN = 0xe3
    SET_CONTINUE = 0xe9
    SET_FIRMWARE_DATA = 0xf0  # upgrade
    UNKNOWN_7 = 0xf1  # upgrade
    UNKNOWN_8 = 0xf2  # upgrade


class Invalid(Exception):
    pass


class Incomplete(Exception):
    pass


class Failure(Exception):
    pass


MESSAGE = "0000ffe1-0000-1000-8000-00805f9b34fb"


class AI9:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self._buf = b""
        self._queue = asyncio.Queue()
        self._listeners = defaultdict(list)
        self._listeners[Op.GET_ASYNC].append(self._get_async_cb)

    async def connect(self, dev):
        self.dev = dev
        await self.dev.connect()
        await self.dev.start_notify(MESSAGE, self._handle_msg)

    def _handle_msg(self, _handle, msg):
        logger.debug("recv %s", codecs.encode(msg, "hex").decode("ascii"))
        self._buf += msg
        while self._buf:
            try:
                op, body = self._unpack()
            except Invalid as e:
                logger.error("Invalid message %s", e, exc_info=True)
                continue
            except Incomplete as e:
                logger.debug("Incomplete message %s", e)
                return
            if op in self._listeners:
                for cb in self._listeners[op]:
                    try:
                        cb(op, body)
                    except Exception:
                        logger.error("Callback exception", exc_info=True)
            else:
                self._queue.put_nowait((op, body))

    def _peek(self, n):
        if len(self._buf) < n:
            raise Incomplete(n)
        return self._buf[:n]

    def _pop(self, n):
        data = self._peek(n)
        self._buf = self._buf[n:]
        return data

    def _unpack(self):
        (start, op, length) = struct.unpack(">HBH", self._peek(5))
        if start != 0x7e7e:
            raise Invalid(self._pop(1))  # resynchronize
        msg = self._pop(5 + length + 3)
        head, body, tail = msg[:5], msg[5:-3], msg[-3:]
        crc_want = crc.compute(head + body)
        crc_have, stop = struct.unpack(">HB", tail)
        if (crc_have, stop) != (crc_want, 0xaa):
            raise Invalid(crc_have, crc_want, stop)
        try:
            op = Op(op)
        except ValueError:
            raise Invalid(op)
        logger.info("recv msg %s %s", op,
                    codecs.encode(body, "hex").decode("ascii"))
        return op, body

    def _pack(self, op, body):
        msg = struct.pack(">HBH", 0x7e7e, op, len(body)) + body
        return msg + struct.pack(">HB", crc.compute(msg), 0xaa)

    async def _write(self, op, body):
        while not self._queue.empty():
            logger.error("Unhandled message %s", self._queue.get_nowait())
        logger.info("send msg %s %s", op,
                    codecs.encode(body, "hex").decode("ascii"))
        msg = self._pack(op, body)
        logger.debug("send %s", codecs.encode(msg, "hex").decode("ascii"))
        try:
            await self.dev.write_gatt_char(MESSAGE, msg)
        except AttributeError:  # loopback
            self._handle_msg(None, self._pack(op, b"\x66"))

    async def _read(self):
        return await self._queue.get()

    async def do(self, op, body):
        await self._write(op, body)
        result, ret = await self._read()
        if result != op:
            raise Failure(result, op)
        return ret

    async def get(self, op, body=b"\x55"):
        return await self.do(op, body)

    async def set(self, op, body=b"\x55", expect=b"\x66"):
        ret = await self.do(op, body)
        if ret != expect:
            raise Failure(ret)

    def _get_async_cb(self, op, body):
        event = {
            0x01: "lid open",
            0x02: "lid close",
            0x0f: "right fiber misplaced",
            0x0d: "left fiber misplaced",
            0x04: "found/aligned",
            0x06: "arc",
            0x07: "splice success",
            0x08: "splice failure",
            0x11: "fiber already spliced",
            0x12: "left face/angle unacceptable",
            0x14: "both face/angle unacceptable",
            0x15: "fiber not found",
            0x31: "left fiber not found",
            0x32: "right fiber not found",
            0x33: "heater warmup",
            0x21: "heat start",
            0x22: "heat done",
        }.get(body[0], "unknown")
        logger.info("event: %s (%#02x) loss=%s dB",
                    event, body[0], body[1]*.01)

    async def move(self, side, direction, steps, speed=9):
        motor, move = {
            "left": {
                "down": (2, 4),
                "left": (0, 2),
                "right": (0, 1),
                "up": (2, 3),
            },
            "right": {
                "down": (3, 4),
                "left": (1, 1),
                "right": (1, 2),
                "up": (3, 3),
            },
            "focus": {
                "left": (5, 2),  # x
                "right": (5, 1),  # x
                "down": (4, 2),  # y?
                "up": (4, 1),  # y?
            },
        }[side][direction]
        await self.set(Op.MOVE_MOTOR, bytes([motor, move, 0, steps, speed]))

    async def _read_img(self, handle):
        buf = b""
        while True:
            op, dat = await self._read()
            if op != Op.GET_RECORD_IMG:
                raise Invalid(op)
            this, total, part = dat[:3]
            if handle != this:
                raise Invalid(handle, this)
            buf += dat[3:]
            if part >= total:
                break
        return buf

    def _decode_img(self, img):
        """Binary run length encoding"""
        out = b""
        for i in range(0, len(img), 2):
            di = int.from_bytes(img[i:i + 2], "big")
            out += bytes([0xff*(di >> 15)]) * (di & 0x7fff)
        if len(out) != 480*640:
            raise Invalid(len(out))
        return out

    async def read_record(self, index):
        await self._write(Op.GET_RECORD, index.to_bytes(2, "big"))
        op, meta = await self._read()
        if op != Op.GET_CURRENT_RECORD:
            raise Invalid(op)
        meta = RecordMeta.unpack(meta)
        img = None
        if meta.image_len:
            img = await self._read_img(meta.image_handle)
            assert len(img) == meta.image_len, (len(img), meta.image_len)
            img = self._decode_img(img)
        return meta, img


def main():
    from argparse import ArgumentParser

    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    p = ArgumentParser()
    p.add_argument("address", nargs="?")
    args = p.parse_args()

    async def run():
        dev = AI9()

        if args.address is None:
            ble = await bleak.BleakScanner.find_device_by_filter(
                lambda dev, addr:
                dev.name and dev.name.startswith("AI-9:")
            )
            await dev.connect(bleak.BleakClient(ble))
        elif args.address != "":
            ble = await bleak.BleakScanner.find_device_by_address(args.address)
            await dev.connect(bleak.BleakClient(ble))

        if True:
            await dev.get(Op.GET_FIBER_SETTINGS, b"\x00")  # body=0x08?
            await dev.get(Op.GET_FIBER_FUNC)  # body=0xff?
            await dev.get(Op.GET_HEAT_TIME)
            await dev.get(Op.GET_FIBER_ADMIN)
            await dev.get(Op.GET_SERIAL)
            await dev.get(Op.GET_DATETIME)
            await dev.get(Op.GET_TOTAL_COUNT)
            await dev.get(Op.GET_CURRENT_COUNT)
            # await dev.set(Op.SET_CONNECTED)

        if True:
            await dev.set(Op.SET_MODE, b"\x01")  # factory mode, manual adjust
            await dev.get(Op.GET_MODE)
            for side in "left right".split():
                for move in "down left right up".split():
                    await dev.move(side, move, steps=100, speed=9)
            # await dev.set(Op.SET_MOTOR_RESET, b"\x01")
            # await dev.set(Op.SET_ARC, b"\x03")
            # await dev.set(Op.SET_CLEAN)
            # await dev.set(Op.SET_CONTINUE)
            await dev.set(Op.SET_MODE, b"\x00")
            await dev.get(Op.GET_MODE)

        if True:
            await dev.set(Op.SET_OPM_VFL_POWERDOWN, b"\xaa")  # enable
            await dev.set(Op.SET_VFL_MODE, b"\x00")
            await dev.set(Op.SET_OPM_UNITS, b"\x00")
            await dev.set(Op.SET_OPM_WAVELENGTH, b"\x04")  # 4:1550
            await dev.get(Op.GET_OPM)
            await dev.set(Op.SET_OPM_VFL_POWERDOWN)  # disable

        if True:
            n = int.from_bytes(await dev.get(Op.GET_RECORD_LAST), "big")
            for i in range(n + 1):
                meta, img = await dev.read_record(i)
                logger.info("image meta %s", meta)
                open("img_{}_meta.bin".format(i), "wb").write(meta.pack())
                if img is not None:
                    open("img_{}.bin".format(i), "wb").write(img)
            # await dev.set(Op.SET_RECORD_READ, (0).to_bytes("big"))

        await asyncio.sleep(1000)

    loop.run_until_complete(run())


if __name__ == "__main__":
    main()
