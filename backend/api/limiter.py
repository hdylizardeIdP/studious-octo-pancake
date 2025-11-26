from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared rate limiter instance for the entire application
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])
