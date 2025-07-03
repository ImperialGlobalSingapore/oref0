#!/usr/bin/env python3

import requests
import time
import sys
import statistics
import json

def time_single_run(server_url, endpoint="/start", run_number=None, show_output=False):
    """
    Time a single HTTP request to the server
    """
    if run_number:
        print(f"Run {run_number}: ", end="", flush=True)
    
    full_url = f"{server_url.rstrip('/')}{endpoint}"
    start_time = time.time()
    
    try:
        # Make HTTP request
        response = requests.get(full_url, timeout=30)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Check if request was successful
        if response.status_code == 200:
            if run_number:
                print(f"{elapsed_time:.3f}s ✅")
            
            # Print output only if requested and it's not a multi-run scenario
            if show_output:
                try:
                    # Pretty print JSON response
                    json_data = response.json()
                    print(f"📄 Response:\n{json.dumps(json_data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"📄 Response:\n{response.text}")
                    
            return elapsed_time, True
        else:
            if run_number:
                print(f"{elapsed_time:.3f}s ❌ (HTTP {response.status_code})")
            else:
                print(f"❌ Request failed with HTTP {response.status_code}")
            
            if show_output:
                print(f"🚨 Error response:\n{response.text}")
                
            return elapsed_time, False
        
    except requests.exceptions.ConnectionError:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if run_number:
            print(f"{elapsed_time:.3f}s ❌ (Connection refused)")
        else:
            print(f"❌ Connection refused - is the server running on {server_url}?")
            
        return elapsed_time, False
    
    except requests.exceptions.Timeout:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if run_number:
            print(f"{elapsed_time:.3f}s ❌ (Timeout)")
        else:
            print(f"❌ Request timed out")
            
        return elapsed_time, False
    
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if run_number:
            print(f"{elapsed_time:.3f}s ❌ (Error: {e})")
        else:
            print(f"❌ Unexpected error: {e}")
            
        return elapsed_time, False

def check_server_health(server_url):
    """
    Check if the server is running and healthy
    """
    try:
        health_url = f"{server_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️  Server health check failed (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        return False

def time_multiple_runs(server_url, endpoint="/start", num_runs=5):
    """
    Time multiple HTTP requests and calculate statistics
    """
    print(f"🚀 Testing {server_url}{endpoint} {num_runs} times...\n")
    
    # Check server health first
    if not check_server_health(server_url):
        print("❌ Server is not healthy. Please check if it's running.")
        return
    
    times = []
    successful_runs = 0
    
    for i in range(1, num_runs + 1):
        elapsed_time, success = time_single_run(server_url, endpoint, i)
        
        if elapsed_time is not None:
            times.append(elapsed_time)
            if success:
                successful_runs += 1
    
    if not times:
        print("❌ No runs completed to analyze")
        return
    
    # Calculate statistics
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Results after {len(times)} requests:")
    print(f"   ✅ Successful: {successful_runs}/{len(times)}")
    print(f"   ⏱️  Average: {avg_time:.3f}s")
    print(f"   🏃 Fastest: {min_time:.3f}s")
    print(f"   🐌 Slowest: {max_time:.3f}s")
    
    if len(times) > 1:
        std_dev = statistics.stdev(times)
        print(f"   📏 Std Dev: {std_dev:.3f}s")
    
    # Calculate requests per second
    rps = successful_runs / sum(times) if times else 0
    print(f"   🚀 Avg RPS: {rps:.2f} req/s")
    
    return avg_time

def compare_endpoints(server_url, num_runs=5):
    """
    Compare performance of different endpoints
    """
    endpoints = ["/start", "/iob", "/meal", "/health"]
    results = {}
    
    print(f"🔄 Comparing endpoint performance ({num_runs} runs each)...\n")
    
    for endpoint in endpoints:
        print(f"Testing {endpoint}...")
        avg_time = time_multiple_runs(server_url, endpoint, num_runs)
        if avg_time:
            results[endpoint] = avg_time
        print()
    
    if results:
        print("📈 Endpoint Performance Comparison:")
        sorted_results = sorted(results.items(), key=lambda x: x[1])
        for endpoint, avg_time in sorted_results:
            print(f"   {endpoint}: {avg_time:.3f}s")

if __name__ == "__main__":
    # Default values
    server_url = "http://localhost:3000"
    endpoint = "/start"
    num_runs = 100
    compare_mode = False
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--compare":
            compare_mode = True
        else:
            server_url = sys.argv[1]
    
    if len(sys.argv) > 2 and not compare_mode:
        endpoint = sys.argv[2]
    
    if len(sys.argv) > 3 and not compare_mode:
        try:
            num_runs = int(sys.argv[3])
        except ValueError:
            print("❌ Number of runs must be an integer")
            sys.exit(1)
    
    if len(sys.argv) > 2 and compare_mode:
        try:
            num_runs = int(sys.argv[2])
        except ValueError:
            print("❌ Number of runs must be an integer")
            sys.exit(1)
    
    # Show usage if needed
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Usage:")
        print("  python3 time_server.py [server_url] [endpoint] [num_runs]")
        print("  python3 time_server.py --compare [num_runs]")
        print("")
        print("Examples:")
        print("  python3 time_server.py                                    # Test localhost:3000/start 5 times")
        print("  python3 time_server.py http://localhost:3000 /start 10    # Test /start 10 times")
        print("  python3 time_server.py http://localhost:3000 /iob 1       # Test /iob once with output")
        print("  python3 time_server.py --compare 3                        # Compare all endpoints 3 times each")
        sys.exit(0)
    
    # Install requests if not available
    try:
        import requests
    except ImportError:
        print("❌ 'requests' library not found. Install with: pip install requests")
        sys.exit(1)
    
    if compare_mode:
        compare_endpoints(server_url, num_runs)
    elif num_runs == 1:
        # Single run with output
        print(f"🎯 Testing {server_url}{endpoint} once...\n")
        elapsed_time, success = time_single_run(server_url, endpoint, show_output=True)
        if elapsed_time:
            print(f"\n⏱️  Execution time: {elapsed_time:.3f} seconds")
    else:
        # Multiple runs with statistics
        time_multiple_runs(server_url, endpoint, num_runs)