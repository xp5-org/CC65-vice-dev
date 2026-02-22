from PIL import Image
from pyzbar.pyzbar import decode

img = Image.open("/testsrc/manual_tests/qr.png").convert("RGB")
results = decode(img)

if not results:
    raise RuntimeError("no qr code detected")

print(results[0].data.decode("utf-8"))
