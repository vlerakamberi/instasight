from app.retry import run_with_retry
from app.utils_logger import setup_logger


def test_run_with_retry_succeeds_after_transient_failures():
    logger = setup_logger("test_retry")
    attempts = {"count": 0}

    def flaky_operation():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary failure")
        return "ok"

    result = run_with_retry(
        operation=flaky_operation,
        operation_name="flaky_operation",
        logger=logger,
        max_attempts=3,
        base_delay_seconds=0.01,
    )

    assert result == "ok"
    assert attempts["count"] == 3
