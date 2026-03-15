"""conftest.py for ordermanagement/tests.

Sets ERROR_RATE=0 so tests that do not patch random.random never trigger
accidental error injection (ERROR_RATE is read inside the function on every
call, so os.environ.setdefault is sufficient here — no temp-file needed).
"""

import os

# Disable the OTEL SDK during unit tests — no collector is running.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("ERROR_RATE", "0")
