import json

def read_and_check_json(file_path, start=0, end=10):
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Print a slice of the JSON data
        keys = list(data.keys())
        sliced_data = {key: data[key] for key in keys[start:end]}
        print("Sliced JSON Data:", sliced_data)
        
        # Indicate if the data was read successfully
        print("JSON data loaded successfully.")
    
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except FileNotFoundError:
        print("File not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Usage example
file_path = '/home/fivos/Desktop/ebooks/pymu_pdf/progress_report.json'
read_and_check_json(file_path, 0, 10)
