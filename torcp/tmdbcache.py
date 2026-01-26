# -*- coding: utf-8 -*-
"""
TMDB query cache for torcp.
Caches TMDB search results to avoid repeated API calls.
"""

import os
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TMDbCache:
    """Cache for TMDB query results with TTL support."""

    CACHE_DIR = "~/.torcp"
    CACHE_FILE = "tmdb_cache.json"
    TTL_DAYS = 30

    def __init__(self, disabled=False):
        self.disabled = disabled
        self.cache = {}
        self._dirty = False
        if not disabled:
            self._load()

    def _get_cache_dir(self):
        return os.path.expanduser(self.CACHE_DIR)

    def _get_cache_path(self):
        return os.path.join(self._get_cache_dir(), self.CACHE_FILE)

    def _load(self):
        """Load cache from disk."""
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache = data.get('entries', {})
                    logger.info(f"Loaded {len(self.cache)} entries from TMDB cache")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load TMDB cache: {e}")
                self.cache = {}

    def _save(self):
        """Save cache to disk."""
        if self.disabled:
            return

        cache_dir = self._get_cache_dir()
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        cache_path = self._get_cache_path()
        try:
            data = {
                'version': '1.0',
                'updated': datetime.now().isoformat(),
                'entries': self.cache
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.cache)} entries to TMDB cache")
        except IOError as e:
            logger.warning(f"Failed to save TMDB cache: {e}")

    def _make_key(self, media_type, title, year):
        """Create normalized cache key."""
        normalized_title = title.lower().strip() if title else ''
        year_str = str(year) if year else '0'
        media_type_str = media_type.lower() if media_type else 'unknown'
        return f"{media_type_str}|{normalized_title}|{year_str}"

    def _is_expired(self, entry):
        """Check if cache entry has expired."""
        if 'timestamp' not in entry:
            return True
        try:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            expiry = timestamp + timedelta(days=self.TTL_DAYS)
            return datetime.now() > expiry
        except (ValueError, TypeError):
            return True

    def get(self, key):
        """Get cached result by key. Returns None if not found or expired."""
        if self.disabled:
            return None

        if key not in self.cache:
            return None

        entry = self.cache[key]
        if self._is_expired(entry):
            logger.debug(f"Cache expired: {key}")
            del self.cache[key]
            self._dirty = True
            return None

        return entry

    def get_by_search(self, media_type, title, year):
        """Get cached result by search parameters."""
        key = self._make_key(media_type, title, year)
        return self.get(key)

    def set(self, key, entry):
        """Store result in cache."""
        if self.disabled:
            return

        entry['timestamp'] = datetime.now().isoformat()
        self.cache[key] = entry
        self._dirty = True

    def set_by_search(self, media_type, title, year, entry):
        """Store result by search parameters."""
        key = self._make_key(media_type, title, year)
        self.set(key, entry)

    def clear(self):
        """Clear all cache entries."""
        self.cache = {}
        self._dirty = True
        # Also delete the file
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                logger.info("TMDB cache cleared")
            except IOError as e:
                logger.warning(f"Failed to delete cache file: {e}")

    def close(self):
        """Save cache to disk if modified."""
        if self._dirty:
            self._save()
            self._dirty = False
