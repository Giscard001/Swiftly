"""Rate-limiting partagé (slowapi).

Déclaré dans un module dédié pour casser le cycle d'import :
main.py importe les routes, qui importent ici rate_limit() — pas de main.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter par IP. Les limites sont posées au niveau des routes via limiter.limit(...).
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def rate_limit():
    """Retourne un décorateur slowapi utilisant la limite configurable (CONV_RATE_LIMIT)."""
    # Import local pour éviter la résolution de settings à l'import du module
    # (utile si la config est rechargée).
    from .config import settings

    return limiter.limit(settings.rate_limit)
