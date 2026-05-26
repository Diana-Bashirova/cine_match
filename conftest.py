import sys
from pathlib import Path

# Гарантируем, что корень проекта стоит в sys.path ПЕРВЫМ
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))