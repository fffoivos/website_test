import os
import time
import subprocess
import psutil
import json
import shutil
from pathlib import Path
from datetime import datetime

def run_docling_test(input_dir, thread_count, report_file):
    """Run docling with specified thread count and monitor performance."""
    output_dir = os.path.join(os.path.dirname(input_dir), f'output_{thread_count}_threads')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Count input files
    input_files = list(Path(input_dir).glob('*.pdf'))
    total_files = len(input_files)
    total_size = sum(f.stat().st_size for f in input_files)
    
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
    
    # Log start of test
    test_log = {
        'thread_count': thread_count,
        'start_time': datetime.now().isoformat(),
        'input_files': total_files,
        'total_size_bytes': total_size,
        'command': ' '.join(cmd),
        'samples': []
    }
    
    start_time = time.time()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    psutil_process = psutil.Process(process.pid)
    
    # Monitor resources
    while process.poll() is None:
        try:
            cpu_percent = psutil_process.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            test_log['samples'].append({
                'timestamp': time.time() - start_time,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent
            })
        except:
            pass
        time.sleep(0.1)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Get output files
    output_files = list(Path(output_dir).glob('*.md'))
    
    # Complete the log
    test_log.update({
        'end_time': datetime.now().isoformat(),
        'duration_seconds': duration,
        'output_files': len(output_files),
        'speed_files_per_second': len(output_files) / duration if duration > 0 else 0,
        'speed_mb_per_second': (total_size / 1024 / 1024) / duration if duration > 0 else 0
    })
    
    # Calculate resource usage statistics
    if test_log['samples']:
        samples = test_log['samples']
        test_log['resource_stats'] = {
            'cpu_avg': sum(s['cpu_percent'] for s in samples) / len(samples),
            'cpu_max': max(s['cpu_percent'] for s in samples),
            'memory_avg': sum(s['memory_percent'] for s in samples) / len(samples),
            'memory_max': max(s['memory_percent'] for s in samples)
        }
    
    # Append to report file
    with open(report_file, 'a') as f:
        json.dump(test_log, f, indent=2)
        f.write('\n')
    
    return test_log

def main():
    input_dir = "/home/fivos/Desktop/extraction_tests/sample_pdfs"
    report_file = "performance_report_5_threads_round_2.json"
    
    # Create fresh report file
    with open(report_file, 'w') as f:
        f.write('')  # Clear file
    
    # Test with 5 threads only
    thread_counts = [5]
    results = []
    
    print(f"Starting performance test on {input_dir}")
    print(f"Results will be saved to {report_file}")
    
    for thread_count in thread_counts:
        print(f"\nTesting with {thread_count} threads...")
        result = run_docling_test(input_dir, thread_count, report_file)
        if result:
            results.append(result)
            print(f"Duration: {result['duration_seconds']:.2f} seconds")
            print(f"Speed: {result['speed_files_per_second']:.2f} files/second")
            print(f"Speed: {result['speed_mb_per_second']:.2f} MB/second")
            if 'resource_stats' in result:
                print(f"Avg CPU: {result['resource_stats']['cpu_avg']:.1f}%")
                print(f"Avg Memory: {result['resource_stats']['memory_avg']:.1f}%")
        else:
            print(f"Test failed for {thread_count} threads")
    
    if results:
        # Find best performance
        best_result = min(results, key=lambda x: x['duration_seconds'])
        total_pdfs = 20500
        estimated_time = (best_result['duration_seconds'] / best_result['input_files']) * total_pdfs
        
        print(f"\nBest performance with {best_result['thread_count']} threads")
        print(f"Estimated time for {total_pdfs} PDFs: {estimated_time/3600:.2f} hours")
        
        # Add summary to report
        with open(report_file, 'a') as f:
            summary = {
                'summary': {
                    'best_thread_count': best_result['thread_count'],
                    'best_speed_files_per_second': best_result['speed_files_per_second'],
                    'best_speed_mb_per_second': best_result['speed_mb_per_second'],
                    'estimated_time_hours': estimated_time/3600
                }
            }
            json.dump(summary, f, indent=2)
    else:
        print("No successful tests to analyze")

if __name__ == "__main__":
    main()
