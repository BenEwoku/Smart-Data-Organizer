# fix_cache.py
import os
import shutil
import sys

print("🧹 Clearing all authentication caches...")

# Windows cache locations
cache_paths = [
    os.path.join(os.environ['USERPROFILE'], '.cache', 'gspread'),
    os.path.join(os.environ['USERPROFILE'], '.cache', 'google-auth'),
    os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'gspread'),
    '__pycache__'
]

for path in cache_paths:
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"✅ Deleted: {path}")
        except Exception as e:
            print(f"⚠️ Could not delete {path}: {e}")

# Kill any running Python processes
os.system('taskkill /f /im python.exe 2>nul')
os.system('taskkill /f /im streamlit.exe 2>nul')

print("\n✅ All caches cleared!")
print("📋 Next steps:")
print("1. Wait 10 seconds")
print("2. Run: streamlit run app.py")
print("3. The sheet should now be created successfully")