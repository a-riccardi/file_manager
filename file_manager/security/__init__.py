"""
This module contains basic functionality to encrypt and decrypt strings,
as well as generating encription keys

e.g.

# example text to encrypt
text = r"{ tags: [ 'text', 'important', 'asd' ] }"

# print original text
print "original text: {}".format(text)

# encrypt the text with an hardware-id dependent key
encrypted = xor_key(text)

# visualize encrypted text
print "encrypted: {}".format(encrypted)

# decrypt the text using the same key
decrypted = xor_key(encrypted)

# visualize decrypted text
print "decrypted: {}".format(decrypted)

"""

import math
import random
import subprocess

CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~ "
FMANAGER = None

def set_manager_hook(file_manager):
    """Saves a reference to the file_manager.py."""

    global FMANAGER
    FMANAGER = file_manager

def generate_base_key(lenght, seed):
    """Generate a random password-like string of desired lenght."""

    random.seed(seed)
    return "".join(random.choice(CHARSET) for i in range(lenght))

def generate_hardware_id():
    """Returns a hardware-specific ID for the current machine."""

    return subprocess.check_output('wmic csproduct get uuid').split('\n')[1].strip()

def xor_string(string, key):
    """XOR a string with a provided key."""

    # adjust the key lenght to be at least the size of the string
    key_min_len = int(math.ceil(float(len(string)) / float(len(key)))) 

    # xor characters
    return ''.join(chr(ord(s)^ord(k)) for s,k in zip(string, key * key_min_len))

def xor_hid(string):
    """XOR a string using an hardware ID-dependent key."""

    return xor_string(string, generate_base_key(1024, generate_hardware_id()))

def xor_key(string):
    """XOR the given string with a password key"""

    global FMANAGER

    try:
        if FMANAGER:
            return xor_string(string, generate_base_key(1024, FMANAGER.config["pw"]))
    except KeyError:
        pass

    return xor_string(string, KEY)

KEY = generate_base_key(1024, generate_hardware_id())

if __name__ == "__main__":
    """Example usage for this module."""

    # example text to encrypt
    text = r"{ tags: [ 'text', 'important', 'asd' ] }"

    # print original text
    print "original text: {}".format(text)

    # encrypt the text with an hardware-id dependent key
    encrypted = xor_key(text)

    # visualize encrypted text
    print "encrypted: {}".format(encrypted)

    # decrypt the text using the same key
    decrypted = xor_key(encrypted)

    # visualize decrypted text
    print "decrypted: {}".format(decrypted)

    print "hardware-ID: {}".format(generate_hardware_id())

    print "test using the same password as the key seed for a 256-chars password 30 times:"
    for i in range(30):
        print generate_base_key(256, "$up3r$Tr0ngPW!")
