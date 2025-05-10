#!/usr/bin/env python3

import os
import json
import time
import psutil
import importlib.util
from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import ast
import asttokens
import re

class CodeAnalyzer:
    def __init__(self, output_dir="results/analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_function_from_response(self, response_text):
        """Extract the Python function from the response text."""
        # Look for Python code block
        code_match = re.search(r'```python\n(.*?)\n```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        return None

    def measure_execution_time(self, func, test_cases):
        """Measure execution time for each test case."""
        times = []
        for case in test_cases:
            start_time = time.perf_counter()
            func(case['input'])
            end_time = time.perf_counter()
            times.append(end_time - start_time)
        return times

    def measure_memory_usage(self, func, test_case):
        """Measure memory usage for a single test case."""
        @memory_profiler.profile
        def wrapper():
            func(test_case['input'])
        return wrapper()

    def analyze_code_complexity(self, code_str):
        """Analyze code complexity metrics."""
        try:
            tree = ast.parse(code_str)
            metrics = {
                'lines': len(code_str.split('\n')),
                'functions': len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]),
                'loops': len([node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))]),
                'conditionals': len([node for node in ast.walk(tree) if isinstance(node, ast.If)])
            }
            return metrics
        except Exception as e:
            print(f"Error analyzing code complexity: {e}")
            return None

    def compare_solutions(self, codex_output, copilot_output, test_cases):
        """Compare solutions from Codex and Copilot."""
        results = {
            'codex': {'times': [], 'memory': [], 'complexity': None},
            'copilot': {'times': [], 'memory': [], 'complexity': None}
        }
        
        # Process each solution
        for source, output in [('codex', codex_output), ('copilot', copilot_output)]:
            code = self.extract_function_from_response(output)
            if code:
                # Create function object from code string
                exec(code, globals())
                func = globals()['trap']  # Assuming the function is named 'trap'
                
                # Measure metrics
                results[source]['times'] = self.measure_execution_time(func, test_cases)
                results[source]['memory'] = self.measure_memory_usage(func, test_cases[0])
                results[source]['complexity'] = self.analyze_code_complexity(code)
        
        return results

    def generate_visualizations(self, results):
        """Generate comparison visualizations."""
        # Execution Time Comparison
        plt.figure(figsize=(10, 6))
        plt.boxplot([results['codex']['times'], results['copilot']['times']], 
                   labels=['Codex', 'Copilot'])
        plt.title('Execution Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.savefig(self.output_dir / 'execution_time_comparison.png')
        plt.close()

        # Code Complexity Comparison
        if results['codex']['complexity'] and results['copilot']['complexity']:
            metrics = ['lines', 'functions', 'loops', 'conditionals']
            codex_values = [results['codex']['complexity'][m] for m in metrics]
            copilot_values = [results['copilot']['complexity'][m] for m in metrics]

            x = range(len(metrics))
            width = 0.35

            plt.figure(figsize=(10, 6))
            plt.bar([i - width/2 for i in x], codex_values, width, label='Codex')
            plt.bar([i + width/2 for i in x], copilot_values, width, label='Copilot')
            plt.xlabel('Metrics')
            plt.ylabel('Count')
            plt.title('Code Complexity Comparison')
            plt.xticks(x, metrics)
            plt.legend()
            plt.savefig(self.output_dir / 'complexity_comparison.png')
            plt.close()

def load_solution(file_path: str) -> str:
    """Load a solution from a file."""
    with open(file_path, 'r') as f:
        return f.read()

def measure_performance(solution_code: str, test_cases: List[Dict[str, Any]], problem_id: str) -> Dict[str, Any]:
    """Measure the performance of a solution."""
    # Create a temporary module
    spec = importlib.util.spec_from_loader('temp_module', loader=None)
    module = importlib.util.module_from_spec(spec)
    
    # Execute the solution code
    exec(solution_code, module.__dict__)
    
    results = {
        'execution_times': [],
        'memory_usage': [],
        'success_rate': 0
    }
    
    total_tests = len(test_cases)
    successful_tests = 0
    
    for test_case in test_cases:
        # Measure memory before
        process = psutil.Process()
        mem_before = process.memory_info().rss
        
        # Measure execution time
        start_time = time.time()
        
        try:
            if problem_id == 'lru_cache':
                # Special handling for LRU Cache
                cache = module.LRUCache(test_case['input']['operations'][1][0][0])
                result = []
                for op, args in zip(test_case['input']['operations'][0][1:], test_case['input']['operations'][1][1:]):
                    if op == 'get':
                        result.append(cache.get(args[0]))
                    else:  # put
                        cache.put(args[0], args[1])
                        result.append(None)
                output = result
            elif problem_id == 'trapping_rain_water':
                # For trapping rain water, input is a list
                output = module.trap(test_case['input'])
            else:
                # For other problems like word ladder, input is a dictionary
                output = module.ladderLength(**test_case['input'])
            
            execution_time = time.time() - start_time
            mem_after = process.memory_info().rss
            
            # Check if output matches expected
            if output == test_case['output']:
                successful_tests += 1
            
            results['execution_times'].append(execution_time)
            results['memory_usage'].append(mem_after - mem_before)
            
        except Exception as e:
            print(f"Error in test case for {problem_id}: {str(e)}")
            results['execution_times'].append(float('inf'))
            results['memory_usage'].append(float('inf'))
    
    results['success_rate'] = (successful_tests / total_tests) * 100
    return results

def analyze_solutions():
    """Analyze solutions from both Codex and Copilot."""
    # Load problem definitions
    with open('data/problem_prompts.json', 'r') as f:
        problems = json.load(f)['prompts']
    
    results = {}
    
    for problem in problems:
        problem_id = problem['id']
        print(f"\nAnalyzing {problem_id}...")
        results[problem_id] = {
            'codex': {},
            'copilot': {}
        }
        
        # Analyze Codex solution
        codex_solution_path = f'results/codex_output/{problem_id}_response.txt'
        if os.path.exists(codex_solution_path):
            print(f"Processing Codex solution for {problem_id}")
            codex_solution = load_solution(codex_solution_path)
            results[problem_id]['codex'] = measure_performance(
                codex_solution,
                problem['examples'],
                problem_id
            )
        
        # Analyze Copilot solution
        copilot_solution_path = f'results/copilot_output/{problem_id}_response.txt'
        if os.path.exists(copilot_solution_path):
            print(f"Processing Copilot solution for {problem_id}")
            copilot_solution = load_solution(copilot_solution_path)
            results[problem_id]['copilot'] = measure_performance(
                copilot_solution,
                problem['examples'],
                problem_id
            )
    
    # Generate visualizations
    generate_visualizations(results)
    
    # Save results
    os.makedirs('results/analysis', exist_ok=True)
    with open('results/analysis/performance_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\nAnalysis Summary:")
    for problem_id, problem_results in results.items():
        print(f"\n{problem_id}:")
        for source in ['codex', 'copilot']:
            if problem_results[source]:
                avg_time = sum(problem_results[source]['execution_times']) / len(problem_results[source]['execution_times'])
                avg_memory = sum(problem_results[source]['memory_usage']) / len(problem_results[source]['memory_usage'])
                print(f"  {source.capitalize()}:")
                print(f"    Success Rate: {problem_results[source]['success_rate']}%")
                print(f"    Average Time: {avg_time:.6f} seconds")
                print(f"    Average Memory: {avg_memory:.0f} bytes")

def generate_visualizations(results: Dict[str, Any]):
    """Generate visualizations for the analysis results."""
    os.makedirs('results/analysis', exist_ok=True)
    
    # Set style
    sns.set_style("whitegrid")
    
    # Create separate plots for each problem and metric
    for problem_id, problem_results in results.items():
        # Execution time comparison
        plt.figure(figsize=(10, 6))
        execution_times = {
            'Codex': problem_results['codex'].get('execution_times', []),
            'Copilot': problem_results['copilot'].get('execution_times', [])
        }
        sns.boxplot(data=pd.DataFrame(execution_times))
        plt.title(f'{problem_id} - Execution Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/analysis/{problem_id}_execution_time.png')
        plt.close()
        
        # Memory usage comparison
        plt.figure(figsize=(10, 6))
        memory_usage = {
            'Codex': problem_results['codex'].get('memory_usage', []),
            'Copilot': problem_results['copilot'].get('memory_usage', [])
        }
        sns.boxplot(data=pd.DataFrame(memory_usage))
        plt.title(f'{problem_id} - Memory Usage Comparison')
        plt.ylabel('Memory (bytes)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/analysis/{problem_id}_memory_usage.png')
        plt.close()
        
        # Create a combined bar plot for success rates
        plt.figure(figsize=(10, 6))
        success_rates = {
            'Codex': problem_results['codex'].get('success_rate', 0),
            'Copilot': problem_results['copilot'].get('success_rate', 0)
        }
        plt.bar(success_rates.keys(), success_rates.values())
        plt.title(f'{problem_id} - Success Rate Comparison')
        plt.ylabel('Success Rate (%)')
        plt.ylim(0, 100)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'results/analysis/{problem_id}_success_rate.png')
        plt.close()

if __name__ == "__main__":
    analyze_solutions() 