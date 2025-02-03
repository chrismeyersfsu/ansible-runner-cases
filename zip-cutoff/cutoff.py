#!/usr/bin/python3

"""
Given the output of ansible-runner transmit <private_data_dir> -p main.yml
Forward the {"kwargs": ...} payload
Forward the {"zipfile": xxxx} payload
Forward PART of the zipfile contents.

Simply close the sending of the zipfile contents.
Usage:
ansible-runner transmit <private_data_dir> -p main.yml | \
        ./cutoff.py | \
        ansible-runner worker > worker.output
"""

import base64
import sys
import time
import json
from json.decoder import JSONDecodeError
import random
import re


class StateMachineError(Exception):
    pass


def read_until_zipfile():
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            sys.stdout.write(line)
            sys.stdout.flush()
            if 'zipfile' in msg:
                return msg['zipfile']
        except JSONDecodeError:
            # Found the zipfile contents line
            if zipfile_length is None:
                raise StateMachineError(f'zipfile message not found in "{line}"')



def read_zipfile(zipfile_length):
    cutoff = random.randint(1, zipfile_length)

    line = sys.stdin.read()
    write_content = line[0:cutoff]
    sys.stdout.write(write_content)
    sys.stdout.flush()

    size = int(4 * ((zipfile_length + 2) / 3))
    return line[size:]



def read_eof(remaining_stdin):
    msg = json.loads(remaining_stdin)
    if 'eof' not in msg:
        raise StateMachineError(f'zipfile eof not found in "{line}"')
    sys.stdout.write(remaining_stdin)
    sys.stdout.flush()


def run():
    zipfile_length = read_until_zipfile()
    remaining_stdin = read_zipfile(zipfile_length)
    #read_eof(remaining_stdin)

run()
