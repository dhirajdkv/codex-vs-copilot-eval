#!/usr/bin/env python3

import os
import time
import json
import memory_profiler
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
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

def main():
    # Test cases for the Trapping Rain Water problem
    test_cases = [
        {'input': [0,1,0,2,1,0,1,3,2,1,2,1], 'expected': 6},
        {'input': [4,2,0,3,2,5], 'expected': 9},
        {'input': [0,1,0,2,1,0,1,3,2,1,2,1] * 100, 'expected': 600},  # Large test case
    ]

    analyzer = CodeAnalyzer()

    # Read outputs
    codex_output = Path('results/codex_output/response_0.txt').read_text()
    copilot_output = Path('results/copilot_output/response_0.txt').read_text()

    # Compare solutions
    results = analyzer.compare_solutions(codex_output, copilot_output, test_cases)

    # Generate visualizations
    analyzer.generate_visualizations(results)

    # Save detailed results
    with open(analyzer.output_dir / 'detailed_results.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main() 