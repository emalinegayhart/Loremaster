import logging
from typing import Set

log = logging.getLogger(__name__)


class TokenBlacklistService:
    """In-memory token blacklist for invalidated tokens."""
    
    def __init__(self):
        self._blacklist: Set[str] = set()
    
    def add_token(self, token: str) -> None:
        """Add token to blacklist (e.g., on logout)."""
        self._blacklist.add(token)
        log.info(f"Token blacklisted (length: {len(self._blacklist)})")
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted."""
        return token in self._blacklist
    
    def remove_token(self, token: str) -> None:
        """Remove token from blacklist."""
        self._blacklist.discard(token)
    
    def clear(self) -> None:
        """Clear entire blacklist."""
        size = len(self._blacklist)
        self._blacklist.clear()
        log.warning(f"Token blacklist cleared ({size} tokens removed)")
    
    def size(self) -> int:
        """Get number of blacklisted tokens."""
        return len(self._blacklist)


_blacklist = TokenBlacklistService()


def get_blacklist() -> TokenBlacklistService:
    """Get global token blacklist instance."""
    return _blacklist
