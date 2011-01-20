import time as _time_builtin
time = _time_builtin.time

__test_time = 0
__test_enabled = False

def test_timing_source():
    global __test_time
    return __test_time

def set_test_time(time):
    global __test_time
    __test_time = time

def sleep(amount):
    global __test_time, __test_enabled
    if __test_enabled:
        __test_time += amount
    else:
        _time_builtin.sleep(amount)

def test_mode(enabled):
    global time, __test_enabled
    if enabled:
        time = test_timing_source
    else:
        time = _time_builtin.time
    __test_enabled = enabled