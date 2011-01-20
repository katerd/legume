# legume. Copyright 2009 Dale Reidy. All rights reserved.
# See LICENSE for details.

import unittest
import ctypes
import sys

class GreenBarRunner(unittest.TextTestRunner):
    FOREGROUND_GREEN= 0x0A
    FOREGROUND_RED  = 0x0C
    FOREGROUND_WHITE= 0x0F
    FOREGROUND_YELLOW=0x0E

    def __init__(self, verbosity=2):
        unittest.TextTestRunner.__init__(self, verbosity=verbosity)
        STD_OUTPUT_HANDLE = -11
        try:
            self.std_out_handle = ctypes.windll.kernel32.GetStdHandle(
                STD_OUTPUT_HANDLE)
        except:
            # Probably non-windows
            self.std_out_handle = None
            pass

    def set_color(self, color):
        try:
            bool = ctypes.windll.kernel32.SetConsoleTextAttribute(
                self.std_out_handle, color)
            return bool
        except:
            # Probably non-windows terminal
            pass

    def run(self, test):
        r = unittest.TextTestRunner.run(self, test)

        if self.std_out_handle is not None:
            failed_count = len(r.failures)
            errored_count = len(r.errors)
            total = r.testsRun
            ok_count = total - (failed_count + errored_count)

            sys.stdout.write('\n[')
            self.set_color(self.FOREGROUND_RED)
            sys.stdout.write('#' * errored_count)
            self.set_color(self.FOREGROUND_YELLOW)
            sys.stdout.write('#' * failed_count)
            self.set_color(self.FOREGROUND_GREEN)
            sys.stdout.write('#' * ok_count)
            self.set_color(self.FOREGROUND_WHITE)
            sys.stdout.write(']\n')