import os
import subprocess
import hashlib

avr_dir = "C:\\Program Files (x86)\\Arduino\\hardware\\tools\\avr\\"
avr_exe = os.path.join(avr_dir, "bin\\avrdude.exe")
avr_conf = os.path.join(avr_dir, "etc\\avrdude.conf")
port = "COM3"
hex_fname = "nano.hex"

def sha256(fname):
    # Generate SHA256 hash from the hex file
    hash_sha256 = hashlib.sha256()
    with open(hex_fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
        print(hash_sha256.hexdigest())

# Call avrdude.exe to extract and save the Arduino's hex file
subprocess.check_call(f"\"{avr_exe}\" -c arduino -p m328p -C \"{avr_conf}\" -P \"{port}\" -b 57600 -U flash:r:{hex_fname}:i")

# Generate SHA256 checksum from the hex file
sha256(hex_fname)

