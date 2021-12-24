# -*- coding:utf-8 -*-

import subprocess
from subprocess import PIPE


class Command:

    def __init__(self):
        self._proc = subprocess
        self._proc = subprocess.run("date", shell=True, stdout=PIPE, stderr=PIPE, text=True)
        date = self._proc.stdout
        print('STDOUT: {}'.format(date))
