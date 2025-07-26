"""
Services package for the ArbitPro Telegram bot.

This package encapsulates helper modules such as the P2P fetcher,
filter engine and aggregator.  It provides convenient import paths
for other parts of the application.
"""

# The __all__ list defines the public API of this package.
__all__ = [
    "aggregator",
    "filter_engine",
    "p2p_fetcher",
]