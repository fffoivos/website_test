import os
import random
import shutil
import time
import subprocess
import psutil
import json
from pathlib import Path
import matplotlib.pyplot as plt

def copy_random_pdfs(source_dir, dest_dir, count=100):
    """Copy random PDFs from source to destination directory."""
    pdf_files = [f for f in Path(source_dir).glob('**/*.pdf')]
    if len(pdf_files) < count:
        raise ValueError(f"Not enough PDF files in source directory. Found {len(pdf_files)}, needed {count}")
    
    # Ensure exactly count files are selected
    selected_files = random.sample(pdf_files, count)
    
    # Clean destination directory
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.makedirs(dest_dir)
    
    # Copy files
    for pdf_file in selected_files:
        dest_path = Path(dest_dir) / pdf_file.name
        shutil.copy2(pdf_file, dest_path)
    
    # Verify copy
    copied_files = list(Path(dest_dir).glob('*.pdf'))
    if len(copied_files) != count:
        raise ValueError(f"Copy verification failed. Expected {count} files, found {len(copied_files)}")
    
    return len(copied_files)

def clean_output_dir(output_dir):
    """Remove all markdown files from output directory."""
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

def monitor_resources(process):
    """Monitor CPU and RAM usage of a process."""
    try:
        cpu_percent = process.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'high_cpu': cpu_percent > 50,
            'high_memory': memory_percent > 50
        }
    except:
        return None

def clean_test_environment():
    """Clean up all test directories."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dirs_to_clean = ['sample_pdfs'] + [f'output_{t}_threads' for t in [4, 8, 12]]
    
    for dir_name in dirs_to_clean:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                print(f"Cleaned up {dir_path}")
            except Exception as e:
                print(f"Error cleaning {dir_path}: {e}")

def run_docling_test(input_dir, thread_count):
    """Run docling with specified thread count and monitor performance."""
    output_dir = os.path.join(os.path.dirname(input_dir), f'output_{thread_count}_threads')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    cmd = [
        'docling',
        input_dir,
        '--to', 'md',
        '--image-export-mode', 'placeholder',
        '--no-ocr',
        '--device', 'cpu',
        '-v',
        '--num-threads', str(thread_count),
        '--output', output_dir
    ]
    
    print(f"\nStarting docling with {thread_count} threads...")
    print(f"Command: {' '.join(cmd)}")
    
    start_time = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    psutil_process = psutil.Process(process.pid)
    
    resource_samples = []
    high_cpu_count = 0
    high_memory_count = 0
    total_samples = 0
    
    try:
        while process.poll() is None:
            resources = monitor_resources(psutil_process)
            if resources:
                resource_samples.append(resources)
                total_samples += 1
                if resources['high_cpu']:
                    high_cpu_count += 1
                if resources['high_memory']:
                    high_memory_count += 1
            time.sleep(0.1)
        
        # Wait for process to complete and get output
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"Error running docling: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Error during execution: {e}")
        process.kill()
        return None
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Calculate percentage of time resources were high
    cpu_high_percent = (high_cpu_count / total_samples * 100) if total_samples > 0 else 0
    memory_high_percent = (high_memory_count / total_samples * 100) if total_samples > 0 else 0
    
    # Verify output
    output_files = os.listdir(output_dir)
    print(f"Generated {len(output_files)} output files")
    
    return {
        'thread_count': thread_count,
        'duration': duration,
        'resource_samples': resource_samples,
        'cpu_high_percent': cpu_high_percent,
        'memory_high_percent': memory_high_percent,
        'files_processed': len(output_files)
    }

def plot_results(results):
    """Plot performance results."""
    thread_counts = [r['thread_count'] for r in results]
    durations = [r['duration'] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.plot(thread_counts, durations, marker='o')
    plt.xlabel('Number of Threads')
    plt.ylabel('Processing Time (seconds)')
    plt.title('Docling Performance vs Thread Count')
    plt.grid(True)
    plt.savefig('performance_results.png')
    
    # Plot resource usage for each thread count
    for result in results:
        thread_count = result['thread_count']
        samples = result['resource_samples']
        
        if samples:
            plt.figure(figsize=(12, 6))
            times = list(range(len(samples)))
            cpu = [s['cpu_percent'] for s in samples]
            memory = [s['memory_percent'] for s in samples]
            
            plt.subplot(1, 2, 1)
            plt.plot(times, cpu)
            plt.title(f'CPU Usage ({thread_count} threads)')
            plt.ylabel('CPU %')
            
            plt.subplot(1, 2, 2)
            plt.plot(times, memory)
            plt.title(f'Memory Usage ({thread_count} threads)')
            plt.ylabel('Memory %')
            
            plt.tight_layout()
            plt.savefig(f'resources_{thread_count}_threads.png')

def main():
    # Clean up previous test environment
    clean_test_environment()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, 'greek_downloads')
    test_dir = os.path.join(base_dir, 'sample_pdfs')
    
    # Create test directory
    os.makedirs(test_dir, exist_ok=True)
    
    # Copy random PDFs
    print("Copying random PDFs...")
    num_copied = copy_random_pdfs(source_dir, test_dir)
    print(f"Copied {num_copied} PDFs for testing")
    
    # Test different thread counts
    thread_counts = [4, 8, 12]
    results = []
    
    for thread_count in thread_counts:
        print(f"\nTesting with {thread_count} threads...")
        result = run_docling_test(test_dir, thread_count)
        if result:
            results.append(result)
            print(f"Duration: {result['duration']:.2f} seconds")
            print(f"Files processed: {result['files_processed']}")
            print(f"High CPU Usage (>50%): {result['cpu_high_percent']:.1f}% of the time")
            print(f"High Memory Usage (>50%): {result['memory_high_percent']:.1f}% of the time")
        else:
            print(f"Test failed for {thread_count} threads")
    
    if results:
        # Save results
        with open('performance_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Plot results
        plot_results(results)
        
        # Calculate estimated total time for 20.5K PDFs
        best_result = min(results, key=lambda x: x['duration'])
        total_pdfs = 20500
        estimated_time = (best_result['duration'] / best_result['files_processed']) * total_pdfs
        print(f"\nBest performance with {best_result['thread_count']} threads")
        print(f"Estimated time for {total_pdfs} PDFs: {estimated_time/3600:.2f} hours")
    else:
        print("No successful tests to analyze")

if __name__ == "__main__":
    main()
