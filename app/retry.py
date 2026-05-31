import time
from typing import Callable, TypeVar


T = TypeVar("T")


def run_with_retry(
    operation: Callable[[], T],
    operation_name: str,
    logger,
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
) -> T:
    """
    Runs an operation with exponential backoff retry.
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - generic retry wrapper
            last_error = exc
            if attempt == max_attempts:
                logger.error(
                    "Operation '%s' failed after %s attempts: %s",
                    operation_name,
                    max_attempts,
                    exc,
                )
                break

            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Operation '%s' failed on attempt %s/%s. Retrying in %.1fs. Error: %s",
                operation_name,
                attempt,
                max_attempts,
                delay,
                exc,
            )
            time.sleep(delay)

    raise last_error
