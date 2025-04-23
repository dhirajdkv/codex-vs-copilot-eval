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

def save_response(response, output_dir):
    """Save the API response to a file."""
    os.makedirs(output_dir, exist_ok=True)
    output_file = Path(output_dir) / f"response_{len(os.listdir(output_dir))}.txt"
    
    with open(output_file, 'w') as f:
        f.write(response)

def test_codex():
    """Test the Codex API with a coding prompt."""
    # Set up OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    print(f"Current working directory: {os.getcwd()}")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        print("Please create a .env file in the project root with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    client = OpenAI()  # This will automatically use the OPENAI_API_KEY from env

    try:
        # Create the API request
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4 as specified
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "Write a Python function to solve the Trapping Rain Water problem"}
            ]
        )
        
        # Extract and save the response
        if response.choices:
            content = response.choices[0].message.content
            print("Response received:")
            print(content)
            
            # Save the response
            save_response(content, "results/codex_output")
        else:
            print("Error: No response content received")
            
    except Exception as e:
        print(f"Error during API call: {str(e)}")

if __name__ == "__main__":
    test_codex() 