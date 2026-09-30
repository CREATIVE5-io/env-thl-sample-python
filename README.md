# C5 3-in-1 Environment Sensor — Python Sample

A standalone Python script that reads the C5 3-in-1 environment sensor (temperature, humidity, light) over Modbus RTU (RS485) using [`modbus_tk`](https://github.com/ljean/modbus-tk).

> [!WARNING]
> **Firmware limitation: only a full-block read is supported.**
>
> The current sensor firmware only responds correctly to a read of **start address `0x21`, length `4`** (function code 3, Read Holding Registers). Reading a single register (e.g. only temperature at `0x21`, length 1) or any other start address or length does not work.
>
> Always read the whole block `0x21`–`0x24` in one request, then pick the values you need from the result. This sample does exactly that.

## Requirements

- Python 3
- An RS485 adapter connected to the sensor
- Python packages:

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Single read from slave id 1
python3 env_3n1_sensor_sample.py --port /dev/ttyUSB0 --id 1

# 10 reads, 2 seconds apart
python3 env_3n1_sensor_sample.py --port /dev/ttyUSB0 --id 1 --interval 2 --count 10

# Read continuously and print the raw Modbus frames (Ctrl+C to stop)
python3 env_3n1_sensor_sample.py --port /dev/ttyUSB0 --count 0 --verbose
```

| Option       | Default        | Description                                         |
|--------------|----------------|-----------------------------------------------------|
| `--port`     | `/dev/ttyUSB0` | RS485 serial port                                   |
| `--id`       | `1`            | Modbus slave id                                     |
| `--timeout`  | `1.0`          | Response timeout in seconds                         |
| `--interval` | `1.0`          | Seconds between reads                               |
| `--count`    | `1`            | Number of reads; `0` = read until Ctrl+C            |
| `--verbose`  | off            | Log raw Modbus request (`->`) / response (`<-`) frames |

The serial settings are fixed at **9600 baud, 8N1** to match the sensor.

Example output:

```
[2026-09-30 14:19:40] temp=25.31degC  hum=48.20%RH  lux=300.00lux  status_3n1=0x0000
```

If a raw value falls outside its valid range, the value is still printed, followed by `(OUT OF RANGE, raw=...)`. Read errors are printed to stderr, and the loop continues with the next read.

## Register map

Holding registers, read with function code 3 as one block (`0x21`, length 4):

| Address | Name         | Type | Scale        | Valid raw range  |
|---------|--------------|------|--------------|------------------|
| `0x21`  | `temp`       | s16  | × 0.01 °C    | -4000 … 12500 (-40.00 … 125.00 °C) |
| `0x22`  | `hum`        | u16  | × 0.01 %RH   | 0 … 10000 (0.00 … 100.00 %RH)      |
| `0x23`  | `lux`        | u16  | × 2 lux      | —                                  |
| `0x24`  | `status_3n1` | u16  | raw (hex)    | —                                  |

This register map mirrors the production driver `env_3n1_sensor.py` in the `smg_modbus` package.

## License

This sample is released under the [MIT License](LICENSE).

It depends on third-party packages that are installed separately from PyPI and are not included in this repository:

| Package     | License           |
|-------------|-------------------|
| `modbus_tk` | LGPL-2.1-or-later |
| `pyserial`  | BSD               |
