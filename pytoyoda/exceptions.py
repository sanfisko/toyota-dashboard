"""Toyota Connected Services API exceptions."""


class ToyotaLoginError(Exception):
    """Raise if a login error happens."""


class ToyotaInvalidUsernameError(Exception):
    """Raise if username is invalid."""


class ToyotaRegionNotSupportedError(Exception):
    """Raise if region is not supported."""


class ToyotaApiError(Exception):
    """Raise if an API error occurs."""


class ToyotaInternalError(Exception):
    """Raise if an internal server error occurs from Toyota."""


class ToyotaActionNotSupportedError(ToyotaApiError):
    """Raise if an action is not supported on a vehicle."""
