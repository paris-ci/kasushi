class KasushiError(Exception):
    """Base class for exceptions in this module."""
    pass


class InvalidConfigurationError(KasushiError):
    """
    Exception raised for errors in the configuration.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class InvalidRequirementsError(KasushiError):
    """
    Exception raised for errors in the requirements.
    It typically means you need to install a missing package.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class IPCInvalidHandlerError(KasushiError):
    """
    Exception raised when calling for an invalid handler.
    You probably need to check the spelling to send_request.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
