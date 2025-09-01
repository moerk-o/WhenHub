#!/usr/bin/env python3
"""Script to run all WhenHub tests individually and collect results."""

import subprocess
import sys
import time
import os

def run_single_test_file(test_file):
    """Run a single test file and return results."""
    print(f'⏳ Running: {test_file}')
    start_time = time.time()
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', test_file, '-v', '--tb=line', '--no-header'
        ], capture_output=True, text=True, timeout=120)
        
        duration = time.time() - start_time
        
        # Parse results
        output_lines = result.stdout.split('\n')
        passed_count = 0
        failed_count = 0
        failed_tests = []
        
        for line in output_lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line):
                if 'PASSED' in line:
                    passed_count += 1
                elif 'FAILED' in line:
                    failed_count += 1
                    test_name = line.split('::')[1].split()[0]
                    failed_tests.append(test_name)
        
        total_tests = passed_count + failed_count
        if result.returncode == 0:
            status = 'PASSED'
            print(f'✅ PASSED: {test_file} - {total_tests} tests ({duration:.1f}s)')
        else:
            status = 'FAILED'
            print(f'❌ FAILED: {test_file} - {passed_count}/{total_tests} passed ({duration:.1f}s)')
            if failed_tests:
                print(f'   Failed: {", ".join(failed_tests[:3])}{"..." if len(failed_tests) > 3 else ""}')
        
        return {
            'file': test_file,
            'status': status,
            'passed': passed_count,
            'failed': failed_count,
            'total': total_tests,
            'duration': duration,
            'failed_tests': failed_tests
        }
        
    except subprocess.TimeoutExpired:
        print(f'⏰ TIMEOUT: {test_file} (120s)')
        return {
            'file': test_file,
            'status': 'TIMEOUT',
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': 120,
            'failed_tests': ['TIMEOUT']
        }
    except Exception as e:
        print(f'💥 ERROR: {test_file} - {e}')
        return {
            'file': test_file,
            'status': 'ERROR',
            'passed': 0,
            'failed': 0,
            'total': 0,
            'duration': 0,
            'failed_tests': [str(e)]
        }

def main():
    # Collect all test files
    test_files = []
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    test_files.sort()
    
    print(f'🧪 Found {len(test_files)} test files')
    print('=' * 80)
    
    results = []
    total_passed = 0
    total_failed = 0
    
    for i, test_file in enumerate(test_files, 1):
        print(f'[{i}/{len(test_files)}]', end=' ')
        result = run_single_test_file(test_file)
        results.append(result)
        total_passed += result['passed']
        total_failed += result['failed']
        print()
    
    # Summary table
    print('\n' + '=' * 80)
    print('📊 COMPREHENSIVE TEST RESULTS SUMMARY')
    print('=' * 80)
    print(f'{"Test File":<50} {"Status":<10} {"Tests":<10} {"Duration":<8}')
    print('-' * 80)
    
    for result in results:
        file_short = result['file'].replace('tests/', '')
        test_info = f"{result['passed']}/{result['total']}" if result['total'] > 0 else "0/0"
        duration_str = f"{result['duration']:.1f}s"
        
        status_icon = {
            'PASSED': '✅',
            'FAILED': '❌', 
            'TIMEOUT': '⏰',
            'ERROR': '💥'
        }.get(result['status'], '❓')
        
        print(f'{file_short:<50} {status_icon} {result["status"]:<8} {test_info:<10} {duration_str:<8}')
        
        if result['failed_tests'] and result['status'] != 'TIMEOUT':
            for failed_test in result['failed_tests'][:2]:  # Show max 2 failed tests
                print(f'{"  └─ Failed:":<50} {failed_test}')
    
    print('-' * 80)
    print(f'TOTAL: {total_passed + total_failed} tests | ✅ {total_passed} passed | ❌ {total_failed} failed')
    
    # Detailed failed tests
    if total_failed > 0:
        print('\n' + '=' * 80)
        print('❌ DETAILED FAILURE LIST')
        print('=' * 80)
        for result in results:
            if result['failed_tests'] and result['status'] not in ['TIMEOUT', 'ERROR']:
                print(f'\n{result["file"]}:')
                for failed_test in result['failed_tests']:
                    print(f'  - {failed_test}')

if __name__ == '__main__':
    main()