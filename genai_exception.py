from google.genai import errors as genai_errors

from typing import Any, NoReturn


class GeminiError(Exception):
    """DotoriGemini에서 발생하는 모든 예외의 기반 클래스."""


class GeminiConfigurationError(GeminiError):
    """Gemini 클라이언트 설정 예외."""


class GeminiResponseError(GeminiError):
    """정상적인 Gemini 응답 데이터를 얻지 못한 경우의 예외."""


class GeminiApiError(GeminiError):
    """Gemini API 응답 코드 기반 예외."""

    is_retryable = False

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_code: str | None = None,
        status: str | None = None,
        details: Any = None,
    ):
        self.status_code = status_code
        self.response_code = response_code
        self.status = status
        self.details = details
        super().__init__(message)


class GeminiRequestError(GeminiApiError):
    """잘못된 요청 또는 사전 조건 미충족 예외."""


class GeminiAuthenticationError(GeminiApiError):
    """API 키 인증 예외."""


class GeminiPermissionError(GeminiApiError):
    """API 리소스 접근 권한 예외."""


class GeminiNotFoundError(GeminiApiError):
    """모델 또는 리소스 탐색 실패 예외."""


class GeminiConflictError(GeminiApiError):
    """요청 충돌 또는 중단 예외."""

    is_retryable = True


class GeminiRateLimitError(GeminiApiError):
    """단기 호출 한도 초과 예외."""

    is_retryable = True


class GeminiQuotaError(GeminiApiError):
    """일일 또는 프로젝트 할당량 초과 예외."""


class GeminiCancelledError(GeminiApiError):
    """요청 취소 예외."""


class GeminiServerError(GeminiApiError):
    """Gemini 내부 서버 예외."""

    is_retryable = True


class GeminiUnsupportedError(GeminiApiError):
    """지원되지 않는 기능 또는 모델 예외."""


class GeminiUnavailableError(GeminiServerError):
    """Gemini 서비스 일시 중단 예외."""


class GeminiTimeoutError(GeminiServerError):
    """Gemini 요청 시간 초과 예외."""


class GeminiExceptionFactory:
    """Gemini SDK 예외를 응답 코드별 도메인 예외로 변환하는 팩토리."""

    response_exception_map = {
        "invalid_request": GeminiRequestError,
        "invalid_argument": GeminiRequestError,
        "failed_precondition": GeminiRequestError,
        "out_of_range": GeminiRequestError,
        "parameter_unknown": GeminiRequestError,
        "authentication": GeminiAuthenticationError,
        "unauthenticated": GeminiAuthenticationError,
        "permission_denied": GeminiPermissionError,
        "not_found": GeminiNotFoundError,
        "model_not_found": GeminiNotFoundError,
        "already_exists": GeminiConflictError,
        "aborted": GeminiConflictError,
        "rate_limit_exceeded": GeminiRateLimitError,
        "resource_exhausted": GeminiRateLimitError,
        "quota_exceeded": GeminiQuotaError,
        "cancelled": GeminiCancelledError,
        "api_error": GeminiServerError,
        "internal": GeminiServerError,
        "unimplemented": GeminiUnsupportedError,
        "service_unavailable": GeminiUnavailableError,
        "unavailable": GeminiUnavailableError,
        "deadline_exceeded": GeminiTimeoutError,
    }
    status_exception_map = {
        400: GeminiRequestError,
        401: GeminiAuthenticationError,
        403: GeminiPermissionError,
        404: GeminiNotFoundError,
        408: GeminiTimeoutError,
        409: GeminiConflictError,
        416: GeminiRequestError,
        429: GeminiRateLimitError,
        499: GeminiCancelledError,
        500: GeminiServerError,
        501: GeminiUnsupportedError,
        503: GeminiUnavailableError,
        504: GeminiTimeoutError,
    }

    @classmethod
    def extract_response_code(cls, error: genai_errors.APIError) -> str | None:
        """SDK 예외 세부 정보에서 API 응답 코드 추출."""
        details = error.details
        if isinstance(details, dict):
            error_details = details.get("error", details)
            response_code = error_details.get("code")
            if isinstance(response_code, str):
                return response_code.lower()

        if isinstance(error.status, str):
            return error.status.lower()

        return None

    @classmethod
    def select_exception(
        cls,
        status_code: int | None,
        response_code: str | None,
    ) -> type[GeminiApiError]:
        """응답 코드와 HTTP 상태에 대응하는 예외 클래스 선택."""
        if response_code in cls.response_exception_map:
            return cls.response_exception_map[response_code]

        if status_code in cls.status_exception_map:
            return cls.status_exception_map[status_code]

        if status_code is not None and 500 <= status_code < 600:
            return GeminiServerError

        if status_code is not None and 400 <= status_code < 500:
            return GeminiRequestError

        return GeminiApiError

    @classmethod
    def create_exception(cls, error: genai_errors.APIError) -> GeminiApiError:
        """Gemini SDK 예외에 대응하는 도메인 예외 생성."""
        status_code = error.code if isinstance(error.code, int) else None
        response_code = cls.extract_response_code(error)
        exception_class = cls.select_exception(status_code, response_code)
        message = error.message or "Gemini API 요청 실패"

        return exception_class(
            message=message,
            status_code=status_code,
            response_code=response_code,
            status=error.status,
            details=error.details,
        )

    @classmethod
    def raise_exception(cls, error: genai_errors.APIError) -> NoReturn:
        """변환된 Gemini 도메인 예외를 원본 예외와 함께 전파."""
        converted_error = cls.create_exception(error)
        error_code = (
            converted_error.response_code
            or converted_error.status_code
            or "GEMINI_API"
        )
        print(f"[ERROR][{error_code}] {converted_error}")
        raise converted_error from error

    @classmethod
    def raise_timeout_exception(cls, error: TimeoutError) -> NoReturn:
        """클라이언트 전체 제한시간 초과 예외 전파."""
        converted_error = GeminiTimeoutError(
            message="Gemini API 요청 제한시간 초과",
            response_code="client_timeout",
        )
        print(f"[ERROR][client_timeout] {converted_error}")
        raise converted_error from error
