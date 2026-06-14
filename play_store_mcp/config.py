import os
from dataclasses import dataclass

@dataclass
class PlayStoreConfig:
    default_country: str = os.getenv("PLAYSTORE_DEFAULT_COUNTRY", "in")
    default_lang: str = os.getenv("PLAYSTORE_DEFAULT_LANG", "en")
    max_reviews: int = int(os.getenv("PLAYSTORE_MAX_REVIEWS", "500"))
    throttle_ms: int = int(os.getenv("PLAYSTORE_THROTTLE_MS", "1000"))

config = PlayStoreConfig()
