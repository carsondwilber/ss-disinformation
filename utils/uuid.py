from secrets import token_bytes
from binascii import hexlify
import time


def uuidv4():
    data = bytearray(token_bytes(16))
    data[6] &= 15
    data[8] &= 63
    data[6] ^= 64
    data[8] ^= 128
    data = hexlify(data).decode('ascii')
    return f'{data[:8]}-{data[8:12]}-{data[12:16]}-{data[16:20]}-{data[20:]}'
