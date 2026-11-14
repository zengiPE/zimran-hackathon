import os
import tempfile

# Point the app at a throwaway SQLite file before app modules are imported.
_tmp = tempfile.mkdtemp(prefix="casefile-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["WEB_BASE_URL"] = ""
