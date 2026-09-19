"""
Attachment Hash Cache (Tech Desk v4 — Section 3.4, 4)

Content-addressed cache keyed by SHA-256 hash of document text.
Stores extraction results so identical attachments (resends, retries, duplicates)
skip re-parsing entirely.

In-memory dict store with LRU-style eviction after MAX_ENTRIES.
"""
import hashlib
import time
from typing import Dict, Any, Optional
from collections import OrderedDict

from backend.services.extractor import extractor

MAX_ENTRIES = 2000


class HashCache:
    """
    SHA-256 content-addressed extraction cache.
    If the same document text has been extracted before, return the cached result
    instead of running the full extraction pipeline again.
    """

    def __init__(self, max_entries: int = MAX_ENTRIES):
        self.max_entries = max_entries
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._stats = {
            "total_lookups": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0
        }

    def _compute_hash(self, text: str) -> str:
        """Compute SHA-256 hash of document text."""
        return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()

    def get_or_extract(
        self, text: str, doc_type_hint: str = "SI"
    ) -> tuple:
        """
        Look up the extraction result by content hash.
        Returns (extraction_dict, cache_hit: bool).

        If cache miss, runs extractor.extract_fields() and stores the result.
        """
        self._stats["total_lookups"] += 1

        if not text or len(text.strip()) == 0:
            # Don't cache empty/blank texts
            result = extractor.extract_fields(text, doc_type_hint)
            self._stats["cache_misses"] += 1
            return result, False

        content_hash = self._compute_hash(text)

        # Cache lookup
        cache_key = f"{content_hash}:{doc_type_hint}"
        if cache_key in self._cache:
            self._stats["cache_hits"] += 1
            # Move to end (most recently used)
            self._cache.move_to_end(cache_key)
            # Return a copy to prevent mutation of cached data
            cached = self._cache[cache_key]
            return dict(cached), True

        # Cache miss — run extraction
        self._stats["cache_misses"] += 1
        result = extractor.extract_fields(text, doc_type_hint)

        # Store in cache
        self._cache[cache_key] = dict(result)
        self._cache.move_to_end(cache_key)

        # Evict oldest if over limit
        while len(self._cache) > self.max_entries:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1

        return result, False

    def get_stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        hit_rate = 0.0
        if self._stats["total_lookups"] > 0:
            hit_rate = round(
                self._stats["cache_hits"] / self._stats["total_lookups"] * 100, 1
            )

        return {
            "total_lookups": self._stats["total_lookups"],
            "cache_hits": self._stats["cache_hits"],
            "cache_misses": self._stats["cache_misses"],
            "hit_rate_pct": hit_rate,
            "current_entries": len(self._cache),
            "max_entries": self.max_entries,
            "evictions": self._stats["evictions"],
            "memory_estimate_kb": round(len(self._cache) * 2.5, 1)  # rough estimate
        }

    def clear(self):
        """Clear the cache entirely."""
        self._cache.clear()
        self._stats = {
            "total_lookups": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "evictions": 0
        }


hash_cache = HashCache()
