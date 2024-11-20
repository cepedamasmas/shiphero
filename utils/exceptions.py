# utils/exceptions.py

class ShipHeroError(Exception):
    """Base exception class for ShipHero integration."""
    pass

class AuthenticationError(ShipHeroError):
    """Raised when there are authentication issues."""
    pass

class RateLimitError(ShipHeroError):
    """Raised when rate limit is exceeded."""
    pass

class APIError(ShipHeroError):
    """Raised when API returns an error."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.status_code = status_code
        self.response = response
        super().__init__(message)

class ValidationError(ShipHeroError):
    """Raised when data validation fails."""
    pass

class ConfigurationError(ShipHeroError):
    """Raised when there are configuration issues."""
    pass