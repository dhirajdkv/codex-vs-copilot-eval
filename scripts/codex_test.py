#!/usr/bin/env python3

import os
import json
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
env_path = find_dotenv()
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

def load_problem_prompt(file_path):
    """Load the problem prompt from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get('prompts', [])
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}")
        return []

def generate_prompt(problem):
    """Generate a detailed prompt for the problem."""
    prompt = f"""Problem: {problem['title']}
Description: {problem['description']}

Function Signature:
{problem['function_signature']}

Examples:
"""
    for example in problem['examples']:
        prompt += f"\nInput: {example['input']}\nOutput: {example['output']}\nExplanation: {example['explanation']}\n"
    
    prompt += "\nConstraints:\n"
    for constraint in problem['constraints']:
        prompt += f"- {constraint}\n"
    
    prompt += "\nPlease provide a Python solution that follows the function signature and handles all the constraints."
    return prompt

def save_response(response, problem_id, output_dir):
    """Save the API response to a file."""
    os.makedirs(output_dir, exist_ok=True)
    output_file = Path(output_dir) / f"{problem_id}_response.txt"
    
    with open(output_file, 'w') as f:
        f.write(response)

def test_codex():
    """Test the Codex API with multiple coding problems."""
    # Set up OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        print("Please create a .env file in the project root with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    client = OpenAI()

    # Load problems
    problems = load_problem_prompt("data/problem_prompts.json")
    
    for problem in problems:
        print(f"\nTesting problem: {problem['title']}")
        
        # Generate prompt
        prompt = generate_prompt(problem)
        
        try:
            # Create the API request
            response = client.chat.completions.create(
                model="gpt-4",  # Using GPT-4
                messages=[
                    {"role": "system", "content": "You are a helpful coding assistant. Provide only the Python code solution without any additional explanation."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract and save the response
            if response.choices:
                content = response.choices[0].message.content
                print(f"Response received for {problem['title']}")
                
                # Save the response
                save_response(content, problem['id'], "results/codex_output")
            else:
                print(f"Error: No response content received for {problem['title']}")
                
        except Exception as e:
            print(f"Error during API call for {problem['title']}: {str(e)}")

if __name__ == "__main__":
    test_codex() 