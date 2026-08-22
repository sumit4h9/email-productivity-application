#!/usr/bin/env python3
"""
Database setup script for the authentication system.
Run this script to initialize the database and create tables.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")

    # Test imports with their actual module names
    package_imports = {
        "alembic": "alembic",
        "sqlalchemy": "sqlalchemy",
        "psycopg2-binary": "psycopg2",
        "python-dotenv": "dotenv",
    }

    missing_packages = []
    for package, import_name in package_imports.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False

    print("✅ All required packages are installed")
    return True


def setup_database():
    """Set up the database and run migrations"""
    print("🚀 Setting up authentication database...")

    # Check if we're in the right directory
    if not Path("alembic.ini").exists():
        print("❌ alembic.ini not found. Please run this script from the backend directory.")
        return False

    # Check requirements
    if not check_requirements():
        return False

    # Check if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  DATABASE_URL environment variable not set")
        print("Please set it to your PostgreSQL connection string:")
        print("export DATABASE_URL='postgresql://user:password@localhost:5432/dbname'")

        # Provide default for development
        default_url = "postgresql://app:app@localhost:5432/app"
        print(f"\nUsing default for development: {default_url}")
        os.environ["DATABASE_URL"] = default_url

    # Generate migration if versions directory is empty
    versions_dir = Path("app/alembic/versions")
    if versions_dir.exists() and not any(versions_dir.glob("*.py")):
        print("\n📝 No migrations found, generating initial migration...")
        if not run_command(
            "alembic revision --autogenerate -m 'Add User model'", "Generating migration"
        ):
            return False

    # Run migrations
    if not run_command("alembic upgrade head", "Running migrations"):
        return False

    print("\n🎉 Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Start your FastAPI server: uvicorn app.main:app --reload")
    print("2. Visit http://localhost:8000/docs to test the API")
    print("3. Test the authentication endpoints")

    return True


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
