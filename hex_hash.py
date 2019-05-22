import os
import subprocess
import hashlib

avr_dir = "C:\\Program Files (x86)\\Arduino\\hardware\\tools\\avr\\"
avr_exe = os.path.join(avr_dir, "bin\\avrdude.exe")
avr_conf = os.path.join(avr_dir, "etc\\avrdude.conf")
port = "COM3"
hex_fname = "nano.hex"

def md5(fname):
    # Generate MD5 hash from the hex file
    hash_md5 = hashlib.md5()
    with open(hex_fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
        print(hash_md5.hexdigest())

# Call avrdude.exe to extract and save the Arduino's hex file
subprocess.check_call(f"\"{avr_exe}\" -c arduino -p m328p -C \"{avr_conf}\" -P \"{port}\" -b 57600 -U flash:r:{hex_fname}:i")
md5(hex_fname)

