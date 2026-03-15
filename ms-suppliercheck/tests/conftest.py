import os

# Disable the OTEL SDK during unit tests — no collector is running.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("ERROR_RATE", "0")
