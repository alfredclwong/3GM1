import os
import subprocess
import hashlib
import base64
import requests

url = 'https://api.github.com/repos/alfredclwong/3GM1/contents/hashes.txt'
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
        return hash_sha256.hexdigest()

# Call avrdude.exe to extract and save the Arduino's hex file
#subprocess.check_call(f"\"{avr_exe}\" -c arduino -p m328p -C \"{avr_conf}\" -P \"{port}\" -b 57600 -U flash:r:{hex_fname}:i")

# Generate SHA256 checksum from the hex file
hash = sha256(hex_fname)
print(hash)

# Verify hash against list of verified hashes on GitHub
req = requests.get(url)
if req.status_code == requests.codes.ok:
    req = req.json()  # the response is a JSON
    # req is now a dict with keys: name, encoding, url, size ...
    # and content. But it is encoded with base64.
    verified_hashes = base64.b64decode(req['content']).decode().split('\n')
    verified_hashes = list(filter(('').__ne__, verified_hashes))
    print(verified_hashes)
    print(hash in verified_hashes)
else:
    print('Content was not found.')
