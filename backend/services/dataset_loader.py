import json
import os
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "inbox.json")

class DatasetLoader:
    def __init__(self, data_path: str = DATA_FILE):
        self.data_path = data_path
        self._cache = None

    def load_inbox(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.data_path):
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_email(self, email_id: str) -> Optional[Dict[str, Any]]:
        emails = self.load_inbox()
        for email in emails:
            if email["id"] == email_id:
                return email
        return None

    def read_attachment_text(self, relative_or_abs_path: str) -> str:
        if os.path.isabs(relative_or_abs_path):
            full_path = relative_or_abs_path
        else:
            # Try workspace root or backend dir
            workspace_root = os.path.dirname(BASE_DIR)
            full_path = os.path.join(workspace_root, relative_or_abs_path)
            if not os.path.exists(full_path):
                full_path = os.path.join(BASE_DIR, os.path.basename(os.path.dirname(relative_or_abs_path)), os.path.basename(relative_or_abs_path))
        
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        return ""

loader = DatasetLoader()
