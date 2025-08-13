#!/usr/bin/env python3
"""
Deployment script for Speech2SQL
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_environment():
    """Check deployment environment"""
    print("🔍 Checking deployment environment...")
    
    # Check if .env exists
    if not Path(".env").exists():
        print("❌ .env file not found. Please run setup.py first")
        return False
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        import streamlit
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False
    
    return True


def run_tests():
    """Run all tests"""
    print("🧪 Running tests...")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=True)
        print("✅ All tests passed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        return False


def build_docker_image():
    """Build Docker image"""
    print("🐳 Building Docker image...")
    try:
        subprocess.run(["docker", "build", "-t", "speech2sql:latest", "."], check=True)
        print("✅ Docker image built successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Docker build failed")
        return False
    except FileNotFoundError:
        print("⚠️  Docker not found. Skipping Docker build")
        return True


def deploy_to_local():
    """Deploy to local environment"""
    print("🚀 Deploying to local environment...")
    
    # Start backend
    print("Starting backend server...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "src.api.main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ])
    
    # Start frontend
    print("Starting frontend server...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501"
    ])
    
    print("✅ Deployment started successfully!")
    print("📱 Backend: http://localhost:8000")
    print("📱 Frontend: http://localhost:8501")
    print("📚 API Docs: http://localhost:8000/docs")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping deployment...")
        backend_process.terminate()
        frontend_process.terminate()


def deploy_to_production():
    """Deploy to production environment"""
    print("🚀 Deploying to production...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is required for production deployment")
        return False
    
    # Build and run with Docker Compose
    try:
        subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
        print("✅ Production deployment completed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Production deployment failed")
        return False


def create_dockerfile():
    """Create Dockerfile if it doesn't exist"""
    dockerfile_path = Path("Dockerfile")
    if dockerfile_path.exists():
        print("✅ Dockerfile already exists")
        return
    
    dockerfile_content = """# Speech2SQL Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/models uploads temp logs

# Expose ports
EXPOSE 8000 8501

# Start command
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    dockerfile_path.write_text(dockerfile_content)
    print("✅ Created Dockerfile")


def create_docker_compose():
    """Create docker-compose.yml if it doesn't exist"""
    compose_path = Path("docker-compose.yml")
    if compose_path.exists():
        print("✅ docker-compose.yml already exists")
        return
    
    compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    environment:
      - DATABASE_TYPE=postgresql
      - POSTGRESQL_URL=postgresql://postgres:password@postgres:5432/speech2sql
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=speech2sql
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
"""
    
    compose_path.write_text(compose_content)
    print("✅ Created docker-compose.yml")


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy Speech2SQL")
    parser.add_argument("--env", choices=["local", "production"], 
                       default="local", help="Deployment environment")
    parser.add_argument("--test", action="store_true", help="Run tests before deployment")
    parser.add_argument("--docker", action="store_true", help="Build Docker image")
    
    args = parser.parse_args()
    
    print("🚀 Speech2SQL Deployment")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Run tests if requested
    if args.test:
        if not run_tests():
            sys.exit(1)
    
    # Create Docker files if needed
    if args.docker or args.env == "production":
        create_dockerfile()
        create_docker_compose()
    
    # Build Docker image if requested
    if args.docker:
        if not build_docker_image():
            sys.exit(1)
    
    # Deploy
    if args.env == "production":
        if not deploy_to_production():
            sys.exit(1)
    else:
        deploy_to_local()


if __name__ == "__main__":
    main() 