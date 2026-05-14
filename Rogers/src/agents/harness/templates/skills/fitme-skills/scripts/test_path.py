from pathlib import Path
import sys

print(f"__file__: {__file__}")
print()

current = Path(__file__)
for i in range(10):
    print(f"{i} parents up: {current}")
    src_dir = current / "src"
    if src_dir.exists():
        print(f"  ✓ Found src dir!")
        print(f"  Adding to path: {current}")
        sys.path.insert(0, str(current))
        break
    current = current.parent

print()
try:
    import src.fitme.models
    print("✓ Imported src.fitme.models successfully!")
except Exception as e:
    print(f"✗ Failed to import: {e}")
