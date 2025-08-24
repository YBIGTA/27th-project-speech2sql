#!/usr/bin/env python3
"""
Integration test script for Speech2SQL system
"""
import sys
import os
import time
import requests
import subprocess
import threading
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings


class IntegrationTest:
    """Integration test runner"""
    
    def __init__(self):
        self.backend_url = f"http://{settings.host}:{settings.port}"
        self.frontend_url = "http://localhost:8501"
        self.backend_process = None
        self.frontend_process = None
    
    def test_backend_startup(self):
        """Test backend server startup"""
        print("🔍 Testing backend startup...")
        
        try:
            # Start backend server
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "src.api.main:app", 
                "--host", settings.host,
                "--port", str(settings.port),
                "--reload"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test health endpoint
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Backend server started successfully!")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Backend startup failed: {e}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔍 Testing API endpoints...")
        
        endpoints = [
            ("/health", "GET"),
            ("/api/v1/audio/upload", "POST"),
            ("/api/v1/query/search", "POST"),
            ("/api/v1/summary/generate", "POST"),
        ]
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.backend_url}{endpoint}", json={}, timeout=5)
                
                if response.status_code in [200, 405, 422]:  # 405 = Method not allowed, 422 = Validation error
                    print(f"✅ {method} {endpoint} - OK")
                else:
                    print(f"⚠️ {method} {endpoint} - {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {method} {endpoint} - Error: {e}")
    
    def test_database_operations(self):
        """Test database operations"""
        print("\n🔍 Testing database operations...")
        
        try:
            from config.database import get_postgresql_engine, create_tables
            from src.database.models import Meeting, Utterance
            
            # Test connection
            engine = get_postgresql_engine()
            with engine.connect() as conn:
                result = conn.execute("SELECT COUNT(*) FROM meetings")
                count = result.fetchone()[0]
                print(f"✅ Database connection OK (meetings: {count})")
            
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False
    
    def test_frontend_startup(self):
        """Test frontend startup"""
        print("\n🔍 Testing frontend startup...")
        
        try:
            # Start frontend server
            frontend_path = Path(__file__).parent.parent / "frontend" / "app.py"
            self.frontend_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", str(frontend_path),
                "--server.port", "8501",
                "--server.headless", "true"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(10)
            
            # Test frontend access
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                print("✅ Frontend server started successfully!")
                return True
            else:
                print(f"❌ Frontend access failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Frontend startup failed: {e}")
            return False
    
    def test_file_structure(self):
        """Test required file structure"""
        print("\n🔍 Testing file structure...")
        
        required_files = [
            "config/settings.py",
            "config/database.py",
            "src/api/main.py",
            "src/database/models.py",
            "src/nlp/text2sql.py",
            "src/audio/whisper_stt.py",
            "frontend/app.py",
            "requirements.txt",
            ".env.example",
            "scripts/setup.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
            else:
                print(f"✅ {file_path}")
        
        if missing_files:
            print(f"\n❌ Missing files: {missing_files}")
            return False
        else:
            print("✅ All required files present!")
            return True
    
    def cleanup(self):
        """Cleanup test processes"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
        
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Speech2SQL Integration Test")
        print("=" * 50)
        
        results = []
        
        # Test file structure
        results.append(("File Structure", self.test_file_structure()))
        
        # Test database
        results.append(("Database", self.test_database_operations()))
        
        # Test backend
        results.append(("Backend", self.test_backend_startup()))
        
        # Test API endpoints
        self.test_api_endpoints()
        
        # Test frontend (optional)
        try:
            results.append(("Frontend", self.test_frontend_startup()))
        except:
            print("⚠️ Frontend test skipped (Streamlit not available)")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results:")
        
        passed = 0
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! System is ready for development.")
        else:
            print("⚠️ Some tests failed. Please check the issues above.")
        
        return passed == total


def main():
    """Main function"""
    tester = IntegrationTest()
    
    try:
        success = tester.run_all_tests()
        return success
    finally:
        tester.cleanup()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 