class NetworkSimplexError(Exception):
    """Base class for solver errors."""


class InfeasibleProblemError(NetworkSimplexError):
    """Raised when artificial flow remains after optimization."""


class UnboundedProblemError(NetworkSimplexError):
    """Raised when an improving direction has no blocking arc."""
