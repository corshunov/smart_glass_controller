import serial

import sycfg as c
import sydt
import syfiles

ser = serial.Serial(c.SERIAL_DEVICE)
ser.baudrate = 115200

ON = "ON"
OFF = "OFF"

def log(state, dt=None):
    if dt is None:
        dt = sydt.now()
    dt_str = sydt.get_str(dt)

    fpath = syfiles.get_log_path(dt)
    with fpath.open('a') as f:
        f.write(f"{dt_str},glstate,{state}\n")

def get():
    if syfiles.glstate_on_fpath.is_file():
        return ON
    else:
        return OFF

def set(state):
    if state == ON:
        ser.write(b'1')
        syfiles.create_file(syfiles.glstate_on_fpath)
    elif state == OFF:
        ser.write(b'0')
        syfiles.remove_file(syfiles.glstate_on_fpath)
    else:
        raise Exception("Invalid 'glstate' argument.")

def set_present():
    if syfiles.set_glstate_on_fpath.is_file():
        syfiles.remove_file(syfiles.set_glstate_on_fpath)
        syfiles.remove_file(syfiles.set_glstate_off_fpath) # in case it is also present
        return True, ON
    elif syfiles.set_glstate_off_fpath.is_file():
        syfiles.remove_file(syfiles.set_glstate_off_fpath)
        return True, OFF

    return False, None

def set_request(state):
    if state == ON:
        syfiles.create_file(syfiles.set_glstate_on_fpath)
    elif state == OFF:
        syfiles.create_file(syfiles.set_glstate_off_fpath)
    else:
        raise Exception("Invalid 'state' argument.")
