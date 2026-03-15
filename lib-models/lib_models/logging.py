import json
import logging


class OtelJsonFormatter(logging.Formatter):
    """JSON log formatter that includes OTEL trace/span IDs.

    Outputs structured JSON logs compatible with Loki JSON parsing.
    The trace_id and span_id fields are injected by the OTEL SDK
    (OTEL_PYTHON_LOG_CORRELATION=true) and read from the LogRecord.
    """

    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "otelTraceID", ""),
            "span_id": getattr(record, "otelSpanID", ""),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)
