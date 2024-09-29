import matplotlib.pyplot as plt
import numpy as np
import os
import csv

# File path for the statistics
statistics_folder = '/home/fivos/Projects/GlossAPI/downloaded_texts/ebooks/ebooks/extracted_pdfs/filtered_extracted_pdfs/cleaned_filtered_extracted_pdfs/statistics'
file_path = os.path.join(statistics_folder, 'removal_statistics.txt')

# Variables to hold sum of averages and count of files
file_data = []

# Read file and extract information
with open(file_path, 'r') as f:
    for line in f:
        # Skip lines that are not file statistics
        if line.startswith("paper"):
            parts = line.split(',')
            file_name = parts[0].split(':')[0].strip()
            avg_chars_per_line = float(parts[2].split()[0])
            
            # Append file data for further processing
            file_data.append((file_name, avg_chars_per_line))

# Extract the average characters per line for all files
avg_chars_per_line_list = np.array([avg for _, avg in file_data])

# Calculate the IQR
Q1 = np.percentile(avg_chars_per_line_list, 25)
Q3 = np.percentile(avg_chars_per_line_list, 75)
IQR = Q3 - Q1

# Separate multipliers for the lower and upper bounds
lower_multiplier = 0.5  # Tighten the lower bound more aggressively
upper_multiplier = 1.5  # Keep or relax the upper bound

# Define the lower and upper bounds for outliers
lower_bound = Q1 - lower_multiplier * IQR
upper_bound = Q3 + upper_multiplier * IQR

# Function to detect outliers based on the adjusted bounds
def is_extreme_value(avg_chars_per_line, lower_bound, upper_bound):
    return avg_chars_per_line < lower_bound or avg_chars_per_line > upper_bound

# Plot the data
def plot_data(avg_chars_per_line_list, lower_bound, upper_bound):
    plt.figure(figsize=(10, 6))
    plt.hist(avg_chars_per_line_list, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    
    # Highlight adjusted IQR bounds
    plt.axvline(lower_bound, color='green', linestyle='dashed', linewidth=2, label=f"Lower Bound: {lower_bound:.2f}")
    plt.axvline(upper_bound, color='green', linestyle='dashed', linewidth=2, label=f"Upper Bound: {upper_bound:.2f}")
    
    plt.title('Distribution of Average Characters per Line (with Separate Bounds)')
    plt.xlabel('Average Characters per Line')
    plt.ylabel('Frequency')
    plt.legend()

    # Save the plot in the statistics subfolder
    plot_file_path = os.path.join(statistics_folder, 'average_chars_per_line_distribution.png')
    plt.savefig(plot_file_path)
    plt.show()

# Detect and print extreme values, and prepare for CSV output
extreme_values = []

for file_name, avg_chars_per_line in file_data:
    if is_extreme_value(avg_chars_per_line, lower_bound, upper_bound):
        extreme_values.append((file_name, avg_chars_per_line))

# Save extreme values to CSV
csv_file_path = os.path.join(statistics_folder, 'extraction_errors.csv')
with open(csv_file_path, mode='w', newline='') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['file_name', 'extract_error'])  # Header
    for file_name, avg_chars_per_line in extreme_values:
        csv_writer.writerow([file_name, 1])  # Marking extract_error as 1

# Print the bounds for reference
print(f"Interquartile Range (IQR): {IQR:.2f}")
print(f"Lower Bound (Q1 - {lower_multiplier} * IQR): {lower_bound:.2f}")
print(f"Upper Bound (Q3 + {upper_multiplier} * IQR): {upper_bound:.2f}\n")
print(f"CSV saved at: {csv_file_path}")

# Plot the data with the adjusted bounds
plot_data(avg_chars_per_line_list, lower_bound, upper_bound)
