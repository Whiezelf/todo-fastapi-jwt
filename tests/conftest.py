import os
import tempfile

# Va impostato PRIMA di importare app.main
os.environ["SECRET_KEY"] = "chiave-solo-per-test-0123456789-abcdefghijklmnopqrstuvwxyz"
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["RATE_LIMIT_ENABLED"] = "false"
