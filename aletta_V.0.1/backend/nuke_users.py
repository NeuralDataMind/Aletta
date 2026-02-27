import os
import shutil
import stat
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.project import User, Project, Dataset

# Helper to fix read-only files on Windows
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def nuke_all_data():
    db = SessionLocal()
    try:
        print("🚀 Initializing Full System Reset...")
        
        # 1. Delete physical files
        if os.path.exists("data"):
            print("📁 Clearing physical 'data/' directory...")
            # Use onerror to handle permission issues
            shutil.rmtree("data", onerror=remove_readonly)
            print("✅ Data directory cleared.")
        
        # Ensure directory structure is restored for the next run
        os.makedirs("data/models", exist_ok=True)

        # 2. Clear Database Tables
        print("🗄️ Purging database records...")
        db.query(Dataset).delete()
        db.query(Project).delete()
        db.query(User).delete()
        
        db.commit()
        print("✨ System Reset Complete. All users and records purged.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during reset: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("⚠️  FINAL WARNING: Delete everything? (y/n): ")
    if confirm.lower() == 'y':
        nuke_all_data()
    else:
        print("Operation aborted.")