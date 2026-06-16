class NyayaLensError(Exception):
    """Base exception for expected NyayaLens errors."""


class UnsupportedDocumentError(NyayaLensError):
    """Raised when an upload type cannot be parsed."""


class VerificationError(NyayaLensError):
    """Raised when a generated report fails safety verification."""
