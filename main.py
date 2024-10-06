from copy import deepcopy
from datetime import datetime, timedelta
from pytz import timezone
import time
import traceback

import cv2
import serial

import utils

allow_sleep = False
is_tz = timezone('Israel')

fps = 20.0
video_length = 5 # seconds

def is_time_to_sleep(dt):
    start_minutes =  7 * 60 + 30 #  7:30
    end_minutes   = 23 * 60 +  0 # 23:00
    
    minutes = dt.hour * 60 + dt.minute
    
    if (minutes < start_minutes) or (minutes > end_minutes):
        return True

    return False

def run_main_loop(vc, ser):
    try:
        utils.prepare_folders()

        dt = datetime.now(is_tz)

        ref_frame = utils.get_ref_frame(vc)
        frame = ref_frame

        video_out = None

        glass_transparent = False
        utils.set_glass_transparent(ser, False)

        log_file = utils.log_fpath.open('w')

        while True:
            prev_dt = dt
            dt = datetime.now(is_tz)

            if allow_sleep and is_time_to_sleep():
                time.sleep(5)
                continue

            prev_frame = frame
            flag, frame = vc.read()
            if not flag:
                raise Exception("Failed to read frame!")

            update_ref_frame_flag = utils.update_ref_frame_requested()
            if update_ref_frame_flag:
                ref_frame = frame
                utils.save_ref_frame(ref_frame, dt)

            if video_out:
                recording_flag = True

                video_out.write(frame)

                if dt > video_end_dt:
                    video_out.release()
                    video_out = None
            else:
                recording_flag = False

                if utils.recording_requested():
                    video_end_dt = dt + timedelta(seconds=video_length)
                    video_out = utils.get_video_writer(vc, dt, fps)

            if utils.both_steps_filled(frame, prev_frame, ref_frame):
                if not glass_transparent:
                    utils.set_glass_transparent(ser, True)
                    glass_transparent = True
            else:
                if glass_transparent:
                    utils.set_glass_transparent(ser, False)
                    glass_transparent = False

            dt_str = dt.strftime("%Y%m%dT%H%M%S")
            delta_str = f"{(dt - prev_dt).total_seconds()*1000:.1f}"
            
            line = (f"{dt_str},"
                    f"{delta_str},"
                    f"{update_ref_frame_flag},"
                    f"{recording_flag},"
                    f"{glass_transparent}\n")
            log_file.write(line)

    except Exception as e:
        vc.release()

        if video_out is not None:
            video_out.release()
            video_out = None

        log_file.close()

        raise(e) from None
        

if __name__ == '__main__':
    try:
        ser = serial.Serial("/dev/ttyUSB0")
        ser.baudrate = 115200

        vc = cv2.VideoCapture(0)
        vc.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        vc.set(cv2.CAP_PROP_EXPOSURE, 40)

        if not vc.isOpened():
            raise Exception("Camera is NOT opened!")

        run_main_loop(vc, ser)

    except KeyboardInterrupt:
        print('\nExit\n')
    except Exception as e:
        tb = traceback.format_exc()
        utils.create_error_file(tb)
