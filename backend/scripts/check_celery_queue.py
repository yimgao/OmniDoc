#!/usr/bin/env python3
"""
Diagnostic script to check Celery queue status
Run this in Railway Shell to diagnose why tasks aren't being processed
"""
import os
import sys

# Add backend directory to path (for src imports)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from src.tasks.celery_app import celery_app
import redis

def check_redis_connection():
    """Check if Redis is accessible"""
    print("=" * 60)
    print("1. Checking Redis Connection")
    print("=" * 60)
    
    redis_url = os.getenv("REDIS_URL", "Not set")
    print(f"REDIS_URL: {redis_url[:50]}..." if len(redis_url) > 50 else f"REDIS_URL: {redis_url}")
    
    try:
        # Test Redis connection
        if "upstash.io" in redis_url or redis_url.startswith("rediss://"):
            test_url = redis_url
            if not test_url.startswith("rediss://"):
                test_url = test_url.replace("redis://", "rediss://", 1)
            
            if "ssl_cert_reqs" not in test_url:
                separator = "?" if "?" not in test_url else "&"
                test_url += f"{separator}ssl_cert_reqs=none"
            
            from urllib.parse import urlparse
            parsed = urlparse(test_url)
            r = redis.Redis(
                host=parsed.hostname,
                port=parsed.port or 6379,
                password=parsed.password,
                ssl=True,
                ssl_cert_reqs=None,
                socket_connect_timeout=5,
                decode_responses=False
            )
        else:
            r = redis.from_url(redis_url, decode_responses=False)
        
        r.ping()
        print("✅ Redis connection successful!")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {type(e).__name__}: {e}")
        return False


def check_celery_broker():
    """Check Celery broker connection"""
    print("\n" + "=" * 60)
    print("2. Checking Celery Broker Connection")
    print("=" * 60)
    
    try:
        broker_url = celery_app.conf.broker_url
        print(f"Broker URL: {broker_url[:50]}..." if len(broker_url) > 50 else f"Broker URL: {broker_url}")
        
        # Try to inspect active tasks
        inspect = celery_app.control.inspect()
        active = inspect.active()
        
        if active:
            print("✅ Celery broker connection successful!")
            print(f"Active workers: {list(active.keys())}")
            return True
        else:
            print("⚠️  No active workers found (this might be normal if worker just started)")
            print("   Trying to check registered tasks...")
            registered = inspect.registered()
            if registered:
                print(f"✅ Found registered workers: {list(registered.keys())}")
                return True
            else:
                print("❌ No workers registered. Is Celery worker running?")
                return False
    except Exception as e:
        print(f"❌ Celery broker check failed: {type(e).__name__}: {e}")
        return False


def check_pending_tasks():
    """Check for pending tasks in queue"""
    print("\n" + "=" * 60)
    print("3. Checking Pending Tasks in Queue")
    print("=" * 60)
    
    try:
        # Get Redis connection
        redis_url = os.getenv("REDIS_URL")
        if "upstash.io" in redis_url or redis_url.startswith("rediss://"):
            test_url = redis_url
            if not test_url.startswith("rediss://"):
                test_url = test_url.replace("redis://", "rediss://", 1)
            
            if "ssl_cert_reqs" not in test_url:
                separator = "?" if "?" not in test_url else "&"
                test_url += f"{separator}ssl_cert_reqs=none"
            
            from urllib.parse import urlparse
            parsed = urlparse(test_url)
            r = redis.Redis(
                host=parsed.hostname,
                port=parsed.port or 6379,
                password=parsed.password,
                ssl=True,
                ssl_cert_reqs=None,
                socket_connect_timeout=5,
                decode_responses=False
            )
        else:
            r = redis.from_url(redis_url, decode_responses=False)
        
        # Check Celery queue (default queue name is 'celery')
        queue_key = "celery"
        queue_length = r.llen(queue_key)
        
        print(f"Queue '{queue_key}' length: {queue_length}")
        
        if queue_length > 0:
            print(f"⚠️  Found {queue_length} pending task(s) in queue!")
            print("   This means tasks are waiting but not being processed.")
            print("   Check if Celery worker is running and connected to the same Redis.")
            return False
        else:
            print("✅ No pending tasks in queue (this is normal if all tasks are processed)")
            return True
            
    except Exception as e:
        print(f"❌ Failed to check queue: {type(e).__name__}: {e}")
        return False


def check_celery_config():
    """Check Celery configuration"""
    print("\n" + "=" * 60)
    print("4. Checking Celery Configuration")
    print("=" * 60)
    
    print(f"Task serializer: {celery_app.conf.task_serializer}")
    print(f"Result serializer: {celery_app.conf.result_serializer}")
    print(f"Accept content: {celery_app.conf.accept_content}")
    print(f"Broker URL: {celery_app.conf.broker_url[:50]}..." if len(celery_app.conf.broker_url) > 50 else f"Broker URL: {celery_app.conf.broker_url}")
    print(f"Result backend: {celery_app.conf.result_backend[:50]}..." if len(celery_app.conf.result_backend) > 50 else f"Result backend: {celery_app.conf.result_backend}")
    
    # Check if tasks are registered
    registered_tasks = list(celery_app.tasks.keys())
    print(f"\nRegistered tasks ({len(registered_tasks)}):")
    for task in registered_tasks:
        if not task.startswith("celery."):
            print(f"  - {task}")
    
    return True


def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 60)
    print("CELERY QUEUE DIAGNOSTIC TOOL")
    print("=" * 60)
    print("\nThis script checks why Celery tasks might not be processed.\n")
    
    results = []
    results.append(("Redis Connection", check_redis_connection()))
    results.append(("Celery Broker", check_celery_broker()))
    results.append(("Pending Tasks", check_pending_tasks()))
    results.append(("Celery Config", check_celery_config()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if not all_passed:
        print("\n⚠️  Some checks failed. Common issues:")
        print("   1. Celery worker not running - check Railway services")
        print("   2. Different REDIS_URL between backend and worker")
        print("   3. Worker not connected to Redis broker")
        print("   4. Tasks in queue but worker not processing them")
    else:
        print("\n✅ All checks passed! If tasks still aren't processing,")
        print("   check Celery worker logs in Railway.")


if __name__ == "__main__":
    main()

