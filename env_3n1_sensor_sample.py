#!/usr/bin/python3
"""
Standalone sample: read the C5 3-in-1 environment sensor (temp / humidity / lux)
over Modbus RTU using modbus_tk.

Register map mirrors env_3n1_sensor.py (holding registers, fCode 3):
    0x21 temp        s16  x0.01 degC   range -4000..12500
    0x22 hum         u16  x0.01 %RH    range 0..10000
    0x23 lux         u16  x2    lux
    0x24 status_3n1  u16  raw

Serial settings are fixed to 9600, 8N1.

Examples:
    python3 env_3n1_sensor_sample.py --port /dev/ttyUSB0 --id 1
    python3 env_3n1_sensor_sample.py --port /dev/ttyUSB0 --id 1 --interval 2 --count 10
    python3 env_3n1_sensor_sample.py --port /dev/ttyUSB0 --verbose   # dump raw Modbus frames
"""

import argparse
import struct
import sys
import time

import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.utils
import serial
from modbus_tk import modbus_rtu

FCODE_R = cst.READ_HOLDING_REGISTERS  # 3

# Fixed sensor serial settings: 9600, 8N1
BAUDRATE = 9600
BYTESIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOPBITS = serial.STOPBITS_ONE

REALTIME_INFO = {
    'temp':       {'address': 0x21, 'type': 's16', 'unit': 0.01, 'range': (-4000, 12500), 'suffix': 'degC'},
    'hum':        {'address': 0x22, 'type': 'u16', 'unit': 0.01, 'range': (0, 10000),     'suffix': '%RH'},
    'lux':        {'address': 0x23, 'type': 'u16', 'unit': 2,    'range': None,            'suffix': 'lux'},
    'status_3n1': {'address': 0x24, 'type': 'u16', 'unit': 1,    'range': None,            'suffix': ''},
}


def open_master(args):
    ser = serial.Serial(port=args.port, baudrate=BAUDRATE, bytesize=BYTESIZE,
                        parity=PARITY, stopbits=STOPBITS, xonxoff=0)
    master = modbus_rtu.RtuMaster(ser)
    master.set_timeout(args.timeout)
    master.set_verbose(args.verbose)
    return master


def decode(name, raw):
    info = REALTIME_INFO[name]
    if info['type'] == 's16':
        raw = struct.unpack('>h', struct.pack('>H', raw))[0]
    rng = info['range']
    in_range = rng is None or rng[0] <= raw <= rng[1]
    return raw, raw * info['unit'], in_range


def read_realtime(master, slave_id):
    # Sensor firmware bug: partial reads are not supported, so always read the
    # full contiguous register block in a single request.
    start = min(r['address'] for r in REALTIME_INFO.values())
    end = max(r['address'] for r in REALTIME_INFO.values())
    regs = master.execute(slave_id, FCODE_R, start, end - start + 1)

    result = {}
    for name, info in REALTIME_INFO.items():
        result[name] = decode(name, regs[info['address'] - start])
    return result


def print_reading(result):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    parts = []
    for name, (raw, value, in_range) in result.items():
        suffix = REALTIME_INFO[name]['suffix']
        if name == 'status_3n1':
            parts.append('{}=0x{:04X}'.format(name, raw))
        else:
            flag = '' if in_range else ' (OUT OF RANGE, raw={})'.format(raw)
            parts.append('{}={:.2f}{}{}'.format(name, value, suffix, flag))
    print('[{}] {}'.format(ts, '  '.join(parts)))


def main():
    parser = argparse.ArgumentParser(description='C5 3-in-1 env sensor sample (modbus_tk)')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='RS485 serial port')
    parser.add_argument('--id', type=int, default=1, help='modbus slave id')
    parser.add_argument('--timeout', type=float, default=1.0)
    parser.add_argument('--interval', type=float, default=1.0, help='seconds between reads')
    parser.add_argument('--count', type=int, default=1, help='number of reads, 0 = forever')
    parser.add_argument('--verbose', action='store_true', help='log raw Modbus request/response frames')
    args = parser.parse_args()

    if args.verbose:
        # modbus_tk only logs frames via its logger; attach a console handler so they're visible.
        modbus_tk.utils.create_logger('console')

    master = open_master(args)
    n = 0
    try:
        while args.count == 0 or n < args.count:
            try:
                print_reading(read_realtime(master, args.id))
            except modbus_tk.modbus.ModbusError as e:
                print('Modbus exception code {}: {}'.format(e.get_exception_code(), e), file=sys.stderr)
            except Exception as e:
                print('Read failed: {}'.format(e), file=sys.stderr)
            n += 1
            if args.count == 0 or n < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        master.close()


if __name__ == '__main__':
    main()
