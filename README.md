# Signalfire AI-9

Library for AI-9 fusion splicer control using bluetooth low energy.
Should run on Linux/Windows/OSX using the `bleak` bluetooth API.

Setup:

```
python3 -m venv py
./py/bin/pip install -r requirements.txt
```

Usage:

```
./py/bin/python ai9.py
```

Example output:

```
INFO:__main__:send msg Op.GET_FIBER_SETTINGS 00
INFO:__main__:recv msg Op.GET_FIBER_SETTINGS 0000641e01140c14281e0100288c8200
INFO:__main__:send msg Op.GET_FIBER_FUNC 55
INFO:__main__:recv msg Op.GET_FIBER_FUNC 02000001010001010a0109000000
INFO:__main__:send msg Op.GET_HEAT_TIME 55
INFO:__main__:recv msg Op.GET_HEAT_TIME 04141211100f0000
INFO:__main__:send msg Op.GET_FIBER_ADMIN 55
INFO:__main__:recv msg Op.GET_FIBER_ADMIN 070507070905040412000000
INFO:__main__:send msg Op.GET_SERIAL 55
INFO:__main__:recv msg Op.GET_SERIAL [...]
INFO:__main__:send msg Op.GET_DATETIME 55
INFO:__main__:recv msg Op.GET_DATETIME 15070d102f29
INFO:__main__:send msg Op.GET_TOTAL_COUNT 55
INFO:__main__:recv msg Op.GET_TOTAL_COUNT 0000000c0000000c
INFO:__main__:send msg Op.GET_CURRENT_COUNT 55
INFO:__main__:recv msg Op.GET_CURRENT_COUNT 0000000c
INFO:__main__:send msg Op.SET_MODE 01
INFO:__main__:recv msg Op.SET_MODE 66
INFO:__main__:send msg Op.GET_MODE 55
INFO:__main__:recv msg Op.GET_MODE 01
INFO:__main__:send msg Op.MOVE_MOTOR 0204006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0002006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0001006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0203006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0304006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0101006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0102006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.MOVE_MOTOR 0303006409
INFO:__main__:recv msg Op.MOVE_MOTOR 66
INFO:__main__:send msg Op.SET_MODE 00
INFO:__main__:recv msg Op.SET_MODE 66
INFO:__main__:send msg Op.GET_MODE 55
INFO:__main__:recv msg Op.GET_MODE 00
INFO:__main__:send msg Op.SET_OPM_VFL_POWERDOWN aa
INFO:__main__:recv msg Op.SET_OPM_VFL_POWERDOWN 66
INFO:__main__:send msg Op.SET_VFL_MODE 00
INFO:__main__:recv msg Op.SET_VFL_MODE 66
INFO:__main__:send msg Op.SET_OPM_UNITS 00
INFO:__main__:recv msg Op.SET_OPM_UNITS 66
INFO:__main__:send msg Op.SET_OPM_WAVELENGTH 04
INFO:__main__:recv msg Op.SET_OPM_WAVELENGTH 66
INFO:__main__:send msg Op.GET_OPM 55
INFO:__main__:recv msg Op.GET_OPM 040000000000
INFO:__main__:send msg Op.SET_OPM_VFL_POWERDOWN 55
INFO:__main__:recv msg Op.SET_OPM_VFL_POWERDOWN 66
INFO:__main__:send msg Op.GET_RECORD_LAST 55
INFO:__main__:recv msg Op.GET_RECORD_LAST 000b
INFO:__main__:send msg Op.GET_RECORD 0000
INFO:__main__:recv msg Op.GET_CURRENT_RECORD 15061d14242e0001000000010000000000000000000000000000000000000000000000000000641e01140c14281e0100288c8200010100070507070905040412000000550000a9
INFO:__main__:image meta RecordMeta(datetime=DateTime(year=21, month=6, day=29, hour=20, minute=36, second=46), failure=0, loss=1, angles=[0, 0, 0], face_quality=1, coordinates=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), settings=FiberSettings(data=(0, 0, 100, 30, 1, 20, 12, 20, 40, 30, 1, 0, 40, 140, 130, 0)), face_detection=1, angle_detection=1, autofocus=0, admin=AdminSettings(et=(7, 5, 7, 7, 9, 5, 4, 4, 18), zero=(0, 0, 0)), charge=85, image_len=0, image_handle=169)
...
```
