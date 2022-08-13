import os
import platform
import subprocess
import time


class CommandManipulator:
    wheel = ['|', '/', '-', '\\']

    def __init__(self, root: bool = False):
        if platform.system() == 'Linux' and root and os.geteuid() != 0:
            print('This script must be run as root')
            raise SystemExit(1)

    def run(self, message: str, command: str, die: bool = True, show_output: bool = False) -> bool:
        temp = '\r [%s] ' + message
        idx = 0

        if platform.system() == 'Windows':
            proc = subprocess.Popen(
                ['powershell.exe', command],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        elif platform.system() == 'Linux':
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                executable='/bin/bash',
                text=True
            )

        while proc.poll() is None:
            if idx < len(self.wheel) - 1:
                idx += 1
            else:
                idx = 0

            print(temp % self.wheel[idx], end='')
            time.sleep(0.1)

        if proc.returncode == 0:
            print(temp % '+')

            if show_output:
                outs, errs = proc.communicate(timeout=15)
                outs_str = outs.decode('utf-8')
                print("Output:")
                print(outs_str.split("Mode")[0])

            return True

        print(temp % 'x', end=': ')
        print(proc.stderr.read().decode('utf-8'), end='')

        if die:
            raise SystemExit(proc.returncode)

        return False
