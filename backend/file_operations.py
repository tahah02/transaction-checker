import json
import os
import tempfile
import csv
from datetime import datetime
from typing import Dict, Any
import threading

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

class SafeFileOperations:
    def __init__(self):
        self._locks = {}
        self._lock = threading.Lock()
    
    def _get_file_lock(self, file_path: str):
        with self._lock:
            if file_path not in self._locks:
                self._locks[file_path] = threading.Lock()
            return self._locks[file_path]
    
    def write_json_atomic(self, file_path: str, data: Dict[str, Any]):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            temp_file = f"{file_path}.tmp"
            
            with open(temp_file, 'w') as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            os.rename(temp_file, file_path)
    
    def read_json_safe(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {}
        
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            with open(file_path, 'r') as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                return json.load(f)
    
    def append_csv_safe(self, file_path: str, row_data: list):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_lock = self._get_file_lock(file_path)
        
        with file_lock:
            file_exists = os.path.isfile(file_path)
            
            with open(file_path, 'a', newline='') as f:
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow(['CustomerID', 'Amount', 'Type', 'Status', 'Timestamp'])
                
                writer.writerow(row_data)
                f.flush()
                os.fsync(f.fileno())

safe_file_ops = SafeFileOperations()

def get_safe_file_ops() -> SafeFileOperations:
    return safe_file_ops