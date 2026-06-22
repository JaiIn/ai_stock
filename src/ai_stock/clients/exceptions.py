"""Safe exception hierarchy for Toss API response handling."""


class TossClientConfigError(ValueError):
    """Raised when client configuration violates foundation requirements."""


class TossApiError(RuntimeError):
    """Base error that stores only non-sensitive response metadata."""

    default_message = "Toss API request failed."

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_code = error_code
        self.request_id = request_id

        details = [message or self.default_message]
        if status_code is not None:
            details.append(f"status={status_code}")
        if error_code:
            details.append(f"code={error_code}")
        if request_id:
            details.append(f"request_id={request_id}")
        super().__init__("; ".join(details))


class TossAuthenticationError(TossApiError):
    default_message = "Toss API authentication failed."


class TossPermissionError(TossApiError):
    default_message = "Toss API permission was denied."


class TossRateLimitError(TossApiError):
    default_message = "Toss API rate limit was exceeded."

    def __init__(self, *args: object, retry_after: str | None = None, **kwargs: object) -> None:
        self.retry_after = retry_after
        super().__init__(*args, **kwargs)


class TossServerError(TossApiError):
    default_message = "Toss API server failed."
