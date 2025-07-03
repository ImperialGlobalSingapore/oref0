#!/usr/bin/env python3

import subprocess
import time
import sys
import statistics

def time_single_run(script_path, run_number=None, show_output=False):
    """
    Time a single run of the shell script
    """
    if run_number:
        print(f"Run {run_number}: ", end="", flush=True)
    
    start_time = time.time()
    
    try:
        # Run the shell script
        result = subprocess.run([script_path], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if run_number:
            print(f"{elapsed_time:.3f}s ✅")
        
        # Print output only if requested and it's not a multi-run scenario
        if show_output and result.stdout:
            print(f"📄 Output:\n{result.stdout}")
            
        return elapsed_time, True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if run_number:
            print(f"{elapsed_time:.3f}s ❌ (exit code {e.returncode})")
        else:
            print(f"❌ Script failed with exit code {e.returncode}")
        
        if show_output and e.stderr:
            print(f"🚨 Error output:\n{e.stderr}")
            
        return elapsed_time, False
    
    except FileNotFoundError:
        print(f"❌ Script '{script_path}' not found")
        return None, False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None, False

def time_multiple_runs(script_path, num_runs=5):
    """
    Time multiple runs of a shell script and calculate statistics
    """
    print(f"🚀 Running {script_path} {num_runs} times...\n")
    
    times = []
    successful_runs = 0
    
    for i in range(1, num_runs + 1):
        elapsed_time, success = time_single_run(script_path, i)
        
        if elapsed_time is not None:
            times.append(elapsed_time)
            if success:
                successful_runs += 1
        else:
            return  # Script not found or other fatal error
    
    if not times:
        print("❌ No successful runs to analyze")
        return
    
    # Calculate statistics
    avg_time = statistics.mean(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Results after {len(times)} runs:")
    print(f"   ✅ Successful: {successful_runs}/{len(times)}")
    print(f"   ⏱️  Average: {avg_time:.3f}s")
    print(f"   🏃 Fastest: {min_time:.3f}s")
    print(f"   🐌 Slowest: {max_time:.3f}s")
    
    if len(times) > 1:
        std_dev = statistics.stdev(times)
        print(f"   📏 Std Dev: {std_dev:.3f}s")
    
    return avg_time

if __name__ == "__main__":
    # Parse command line arguments
    script_path = "./example.sh"
    num_runs = 100
    
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            num_runs = int(sys.argv[2])
        except ValueError:
            print("❌ Number of runs must be an integer")
            sys.exit(1)
    
    if num_runs == 1:
        # Single run with output
        elapsed_time, success = time_single_run(script_path, show_output=True)
        if elapsed_time:
            print(f"⏱️  Execution time: {elapsed_time:.3f} seconds")
    else:
        # Multiple runs with statistics
        time_multiple_runs(script_path, num_runs)