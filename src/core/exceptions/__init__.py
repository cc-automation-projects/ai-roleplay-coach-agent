"""Domain exceptions for the coaching system."""


class CoachHubError(Exception):
    """Base exception for all coach hub errors."""


class ConfigurationError(CoachHubError):
    """Configuration or environment error."""


class NotFoundError(CoachHubError):
    """Entity not found."""

    def __init__(self, entity_type: str, entity_id: str, message: str | None = None) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = message or f"{entity_type} not found: {entity_id}"
        super().__init__(self.message)


class ValidationError(CoachHubError):
    """Domain validation failed."""


class DuplicateError(CoachHubError):
    """Entity already exists."""


class InfrastructureError(CoachHubError):
    """Infrastructure-level error (DB, network, etc.)."""


class AIServiceError(CoachHubError):
    """AI model or service error."""


class AuthorizationError(CoachHubError):
    """User not authorized for this operation."""


class BusinessRuleViolationError(CoachHubError):
    """A business rule was violated."""


class AITimeoutError(CoachHubError):
    """AI model or service timeout."""


class CircuitBreakerOpenError(CoachHubError):
    """Circuit breaker is open; call rejected."""

    def __init__(
        self,
        circuit_name: str,
        failure_count: int,
        retry_after: float = 0.0,
        message: str | None = None,
    ) -> None:
        self.circuit_name = circuit_name
        self.failure_count = failure_count
        self.retry_after = retry_after
        self.message = message or (
            f"Circuit breaker '{circuit_name}' is open "
            f"(failures={failure_count}, retry_after={retry_after:.1f}s)"
        )
        super().__init__(self.message)


class CoachError(CoachHubError):
    """Coach agent processing error."""


class CuratorError(CoachHubError):
    """Curator agent processing error."""


__all__ = [
    "AIServiceError",
    "AITimeoutError",
    "AuthorizationError",
    "BusinessRuleViolationError",
    "CircuitBreakerOpenError",
    "CoachError",
    "CoachHubError",
    "ConfigurationError",
    "CuratorError",
    "DuplicateError",
    "InfrastructureError",
    "NotFoundError",
    "ValidationError",
]
