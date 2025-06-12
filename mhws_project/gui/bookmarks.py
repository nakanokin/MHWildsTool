import json
import os
from typing import List, Dict

# BOOKMARKS_FILE = "data/bookmarks.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKMARKS_FILE = os.path.join(BASE_DIR, "..", "data", "bookmarks.json")
MAX_BOOKMARKS = 10


def load_bookmarks() -> List[Dict]:
    if not os.path.exists(BOOKMARKS_FILE):
        return []
    with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bookmarks(bookmarks: List[Dict]) -> None:
    with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
        json.dump(bookmarks, f, ensure_ascii=False, indent=2)


def add_bookmark(new_entry: Dict) -> None:
    bookmarks = load_bookmarks()

    # すでに同じ名前が存在する場合は上書き
    bookmarks = [b for b in bookmarks if b["name"] != new_entry["name"]]

    bookmarks.insert(0, new_entry)  # 新しいものを先頭に
    if len(bookmarks) > MAX_BOOKMARKS:
        bookmarks = bookmarks[:MAX_BOOKMARKS]
    save_bookmarks(bookmarks)


def delete_bookmark(name: str) -> None:
    bookmarks = load_bookmarks()
    bookmarks = [b for b in bookmarks if b["name"] != name]
    save_bookmarks(bookmarks)


def clear_all_bookmarks() -> None:
    save_bookmarks([])
