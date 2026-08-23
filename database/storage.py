import os
import json
import secrets
import threading
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from config.settings import data_dir, storage_backend, mongodb_uri

logger = logging.getLogger("market_scout.storage")


def generate_analysis_id() -> str:
    """Generates a 24-character hex ID (compatible with standard ObjectId format)."""
    return secrets.token_hex(12)


class StorageBackend(ABC):
    @abstractmethod
    def save_analysis(self, doc_dict: Dict[str, Any], custom_id: Optional[str] = None) -> str:
        """Create a new analysis document and return its ID string."""
        pass

    @abstractmethod
    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis by string ID."""
        pass

    @abstractmethod
    def update_analysis(self, analysis_id: str, updates: Dict[str, Any]) -> bool:
        """Update fields in an existing analysis."""
        pass

    @abstractmethod
    def push_evidence(self, analysis_id: str, evidence_item: Dict[str, Any]) -> bool:
        """Atomically append a search evidence item to an analysis in real time."""
        pass

    @abstractmethod
    def save_search_cache(self, key: str, data: str) -> None:
        """Cache search result by normalized key."""
        pass

    @abstractmethod
    def get_search_cache(self, key: str) -> Optional[str]:
        """Retrieve cached search result."""
        pass


class LocalFileStorage(StorageBackend):
    def __init__(self, base_dir: str = data_dir):
        self.base_dir = base_dir
        self.analyses_dir = os.path.join(self.base_dir, "analyses")
        self.cache_file = os.path.join(self.base_dir, "search_cache.json")
        self._lock = threading.Lock()
        
        os.makedirs(self.analyses_dir, exist_ok=True)
        if not os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
            except Exception as e:
                logger.error("Failed to initialize search cache file: %s", e)

    def _file_path(self, analysis_id: str) -> str:
        # Sanitize ID to prevent directory traversal
        clean_id = os.path.basename(str(analysis_id))
        return os.path.join(self.analyses_dir, f"{clean_id}.json")

    def save_analysis(self, doc_dict: Dict[str, Any], custom_id: Optional[str] = None) -> str:
        analysis_id = custom_id or doc_dict.get("_id") or doc_dict.get("id") or generate_analysis_id()
        doc_dict["_id"] = str(analysis_id)
        if "id" in doc_dict:
            doc_dict["id"] = str(analysis_id)

        file_path = self._file_path(analysis_id)
        with self._lock:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(doc_dict, f, indent=2, default=str)
        
        logger.info("Saved analysis locally to %s", file_path)
        return str(analysis_id)

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        file_path = self._file_path(analysis_id)
        if not os.path.isfile(file_path):
            return None
        try:
            with self._lock:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_id"] = str(data.get("_id", analysis_id))
                    return data
        except Exception as e:
            logger.error("Error reading analysis file %s: %s", file_path, e)
            return None

    def update_analysis(self, analysis_id: str, updates: Dict[str, Any]) -> bool:
        file_path = self._file_path(analysis_id)
        with self._lock:
            if not os.path.isfile(file_path):
                return False
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data.update(updates)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                return True
            except Exception as e:
                logger.error("Error updating analysis %s: %s", analysis_id, e)
                return False

    def push_evidence(self, analysis_id: str, evidence_item: Dict[str, Any]) -> bool:
        file_path = self._file_path(analysis_id)
        with self._lock:
            if not os.path.isfile(file_path):
                return False
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "evidence" not in data or not isinstance(data["evidence"], list):
                    data["evidence"] = []
                data["evidence"].append(evidence_item)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                return True
            except Exception as e:
                logger.error("Error pushing evidence to %s: %s", analysis_id, e)
                return False

    def save_search_cache(self, key: str, data: str) -> None:
        with self._lock:
            try:
                cache = {}
                if os.path.exists(self.cache_file):
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                cache[key] = data
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(cache, f, indent=2)
            except Exception as e:
                logger.warning("Failed to save search cache: %s", e)

    def get_search_cache(self, key: str) -> Optional[str]:
        with self._lock:
            try:
                if os.path.exists(self.cache_file):
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                        return cache.get(key)
            except Exception:
                return None
        return None


class MongoStorage(StorageBackend):
    def __init__(self, uri: str = mongodb_uri):
        from database.db import db
        self.db = db

    def save_analysis(self, doc_dict: Dict[str, Any], custom_id: Optional[str] = None) -> str:
        from bson import ObjectId
        # Strip string _id if creating new
        if "_id" in doc_dict and isinstance(doc_dict["_id"], str):
            del doc_dict["_id"]
        result = self.db.analyses.insert_one(doc_dict)
        return str(result.inserted_id)

    def get_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            query = {"_id": ObjectId(analysis_id)}
        except (InvalidId, Exception):
            query = {"_id": analysis_id}
            
        doc = self.db.analyses.find_one(query)
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def update_analysis(self, analysis_id: str, updates: Dict[str, Any]) -> bool:
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            query = {"_id": ObjectId(analysis_id)}
        except (InvalidId, Exception):
            query = {"_id": analysis_id}
            
        res = self.db.analyses.update_one(query, {"$set": updates})
        return res.modified_count > 0 or res.matched_count > 0

    def push_evidence(self, analysis_id: str, evidence_item: Dict[str, Any]) -> bool:
        from bson import ObjectId
        from bson.errors import InvalidId
        try:
            query = {"_id": ObjectId(analysis_id)}
        except (InvalidId, Exception):
            query = {"_id": analysis_id}
            
        res = self.db.analyses.update_one(query, {"$push": {"evidence": evidence_item}})
        return res.modified_count > 0 or res.matched_count > 0

    def save_search_cache(self, key: str, data: str) -> None:
        try:
            self.db.search_cache.update_one(
                {"key": key},
                {"$set": {"data": data, "updated_at": datetime.datetime.now().ctime()}},
                upsert=True
            )
        except Exception as e:
            logger.warning("Failed to save search cache in Mongo: %s", e)

    def get_search_cache(self, key: str) -> Optional[str]:
        try:
            doc = self.db.search_cache.find_one({"key": key})
            return doc.get("data") if doc else None
        except Exception:
            return None


# Global singleton instance
_storage_instance: Optional[StorageBackend] = None

def get_storage() -> StorageBackend:
    global _storage_instance
    if _storage_instance is None:
        if storage_backend == "mongodb" and mongodb_uri:
            try:
                _storage_instance = MongoStorage()
                logger.info("Storage initialized with MongoDB backend")
            except Exception as e:
                logger.warning("Failed to initialize MongoDB storage (%s). Falling back to LocalFileStorage.", e)
                _storage_instance = LocalFileStorage()
        else:
            _storage_instance = LocalFileStorage()
            logger.info("Storage initialized with LocalFileStorage backend (data_dir: %s)", data_dir)
            
    return _storage_instance
