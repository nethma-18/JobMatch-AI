import pytest
import mongomock
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Define Async Mock Wrapper for mongomock
class AsyncMockCursor:
    def __init__(self, sync_cursor):
        self.sync_cursor = sync_cursor
        
    def sort(self, *args, **kwargs):
        self.sync_cursor = self.sync_cursor.sort(*args, **kwargs)
        return self
        
    def skip(self, *args, **kwargs):
        self.sync_cursor = self.sync_cursor.skip(*args, **kwargs)
        return self
        
    def limit(self, *args, **kwargs):
        self.sync_cursor = self.sync_cursor.limit(*args, **kwargs)
        return self
        
    async def to_list(self, length=None):
        return list(self.sync_cursor)

class AsyncMockCollection:
    def __init__(self, sync_collection):
        self.sync_collection = sync_collection

    async def find_one(self, *args, **kwargs):
        return self.sync_collection.find_one(*args, **kwargs)

    async def insert_one(self, *args, **kwargs):
        return self.sync_collection.insert_one(*args, **kwargs)

    async def update_one(self, *args, **kwargs):
        return self.sync_collection.update_one(*args, **kwargs)

    async def update_many(self, *args, **kwargs):
        return self.sync_collection.update_many(*args, **kwargs)

    async def delete_one(self, *args, **kwargs):
        return self.sync_collection.delete_one(*args, **kwargs)

    async def count_documents(self, *args, **kwargs):
        return self.sync_collection.count_documents(*args, **kwargs)

    def find(self, *args, **kwargs):
        cursor = self.sync_collection.find(*args, **kwargs)
        return AsyncMockCursor(cursor)

class AsyncMockDatabase:
    def __init__(self, sync_db):
        self.sync_db = sync_db
        
    def __getitem__(self, name):
        return AsyncMockCollection(self.sync_db[name])
        
    async def command(self, *args, **kwargs):
        if args and args[0] == "ping":
            return {"ok": 1.0}
        return self.sync_db.command(*args, **kwargs)


@pytest.fixture
def mock_db():
    sync_client = mongomock.MongoClient()
    sync_db = sync_client.jobmatch_ai_test
    return AsyncMockDatabase(sync_db)


@pytest.fixture(autouse=True)
def override_db_dependency(mock_db, monkeypatch):
    from app.core.database import get_db
    from app.main import app
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
