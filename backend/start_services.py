#!/usr/bin/env python3
"""
Service startup script for Gmail Sync Backend
This script helps start all required services for the Gmail sync system
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(command, description, background=False):
    """Run a command and handle errors"""
    print(f"\n🚀 {description}")
    print(f"Command: {command}")
    
    try:
        if background:
            # Run in background
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"✅ {description} started in background (PID: {process.pid})")
            return process
        else:
            # Run in foreground
            result = subprocess.run(command, shell=True, check=True, text=True)
            print(f"✅ {description} completed successfully")
            return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return None
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return None

def check_service_health():
    """Check if required services are running"""
    print("\n🔍 Checking service health...")
    
    # Check Redis
    try:
        result = subprocess.run("redis-cli ping", shell=True, capture_output=True, text=True)
        if result.returncode == 0 and "PONG" in result.stdout:
            print("✅ Redis is running")
        else:
            print("❌ Redis is not running")
            return False
    except:
        print("❌ Redis is not running")
        return False
    
    # Check database connection
    try:
        result = subprocess.run(
            "python -c \"from app.db.session import test_database_connection; print('Database:', test_database_connection())\"",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0 and "True" in result.stdout:
            print("✅ Database connection is healthy")
        else:
            print("❌ Database connection failed")
            return False
    except:
        print("❌ Database connection failed")
        return False
    
    return True

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 Gmail Sync Backend - Service Startup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Check service health
    if not check_service_health():
        print("\n❌ Required services are not healthy. Please start Redis and ensure database is accessible.")
        sys.exit(1)
    
    print("\n📋 Available startup options:")
    print("1. Start FastAPI server only")
    print("2. Start Celery worker only")
    print("3. Start Celery Beat only")
    print("4. Start all services (FastAPI + Celery Worker + Celery Beat)")
    print("5. Start development environment (all services + auto-reload)")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    processes = []
    
    try:
        if choice == "1":
            # Start FastAPI server
            run_command(
                "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
                "Starting FastAPI server"
            )
            
        elif choice == "2":
            # Start Celery worker
            run_command(
                "celery -A app.core.celery_app worker --loglevel=info --concurrency=4",
                "Starting Celery worker"
            )
            
        elif choice == "3":
            # Start Celery Beat
            run_command(
                "celery -A app.core.celery_app beat --loglevel=info",
                "Starting Celery Beat scheduler"
            )
            
        elif choice == "4":
            # Start all services
            print("\n🔄 Starting all services...")
            
            # Start Celery worker in background
            worker_process = run_command(
                "celery -A app.core.celery_app worker --loglevel=info --concurrency=4",
                "Starting Celery worker",
                background=True
            )
            if worker_process:
                processes.append(worker_process)
            
            time.sleep(2)  # Give worker time to start
            
            # Start Celery Beat in background
            beat_process = run_command(
                "celery -A app.core.celery_app beat --loglevel=info",
                "Starting Celery Beat scheduler",
                background=True
            )
            if beat_process:
                processes.append(beat_process)
            
            time.sleep(2)  # Give beat time to start
            
            # Start FastAPI server in foreground
            run_command(
                "uvicorn app.main:app --host 0.0.0.0 --port 8000",
                "Starting FastAPI server"
            )
            
        elif choice == "5":
            # Start development environment
            print("\n🔄 Starting development environment...")
            
            # Start Celery worker in background
            worker_process = run_command(
                "celery -A app.core.celery_app worker --loglevel=info --concurrency=2",
                "Starting Celery worker (dev mode)",
                background=True
            )
            if worker_process:
                processes.append(worker_process)
            
            time.sleep(2)
            
            # Start Celery Beat in background
            beat_process = run_command(
                "celery -A app.core.celery_app beat --loglevel=info",
                "Starting Celery Beat scheduler (dev mode)",
                background=True
            )
            if beat_process:
                processes.append(beat_process)
            
            time.sleep(2)
            
            # Start FastAPI server with reload
            run_command(
                "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
                "Starting FastAPI server (dev mode with auto-reload)"
            )
            
        else:
            print("❌ Invalid choice. Please run the script again.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate background processes
        for process in processes:
            try:
                process.terminate()
                print(f"✅ Terminated process {process.pid}")
            except:
                pass
        
        print("✅ All services stopped")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Clean up background processes
        for process in processes:
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    main()
