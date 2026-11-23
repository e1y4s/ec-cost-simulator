import os
import sys

ROOT = os.path.dirname(__file__)
for path in (os.path.join(ROOT, "src"),):
    if path not in sys.path:
        sys.path.insert(0, path)
