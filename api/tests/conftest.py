import os
import tempfile

# Point the app at a throwaway SQLite file and no LLM key before app modules are imported.
_tmp = tempfile.mkdtemp(prefix="casefile-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["PUBLIC_WEB_URL"] = "https://web.test"
os.environ["ANTHROPIC_API_KEY"] = ""
