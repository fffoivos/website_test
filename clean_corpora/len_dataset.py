import pandas as pd

def print_dataset_length(csv_path):
    """
    Reads a CSV file and prints the number of rows in the dataset.
    
    Parameters:
    - csv_path: Path to the CSV file.
    """
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(csv_path)
        
        # Get the number of rows
        num_rows = len(df)
        
        # Print the result
        print(f"The dataset contains {num_rows} rows.")
        
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
    except pd.errors.EmptyDataError:
        print("Error: The CSV file is empty.")
    except pd.errors.ParserError:
        print("Error: There was a problem parsing the CSV file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Replace 'input.csv' with the path to your actual CSV file
    csv_file_path = '/home/fivos/sxolika_dataset.csv'
    print_dataset_length(csv_file_path)
