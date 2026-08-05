"""MinuteFlow domain exceptions."""


class MinuteFlowError(Exception):
    """Base class for expected MinuteFlow failures."""


class InputValidationError(MinuteFlowError):
    """Raised before a model call when the source input is invalid."""


class ConfigurationError(MinuteFlowError):
    """Raised when live runtime configuration is incomplete or invalid."""


class AgentContractError(MinuteFlowError):
    """Raised when an Agent returns structurally unsafe output."""


class AgentRuntimeError(MinuteFlowError):
    """Raised when an Agent SDK run fails."""
