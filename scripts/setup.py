#!/usr/bin/env python3
"""
Project setup script for Speech2SQL
"""
import os
import sys
import subprocess
from pathlib import Path


def create_directories():
    """Create necessary directories"""
    directories = [
        "data/raw",
        "data/processed", 
        "data/models",
        "data/datasets",
        "uploads",
        "temp",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")


def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)


def setup_environment():
    """Setup environment file"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from template")
        print("⚠️  Please update .env file with your API keys and settings")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env file created. Please create one manually")


def check_database():
    """Check database connection"""
    print("🔍 Checking database connection...")
    # TODO: Implement database connection check
    print("⚠️  Database connection check not implemented yet")


def main():
    """Main setup function"""
    print("🚀 Setting up Speech2SQL project...")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    install_dependencies()
    
    # Setup environment
    print("\n⚙️  Setting up environment...")
    setup_environment()
    
    # Check database
    print("\n🗄️  Checking database...")
    check_database()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update .env file with your API keys")
    print("2. Start the backend: python -m uvicorn src.api.main:app --reload")
    print("3. Start the frontend: streamlit run frontend/app.py")
    print("4. Open http://localhost:8501 in your browser")


if __name__ == "__main__":
    main() 