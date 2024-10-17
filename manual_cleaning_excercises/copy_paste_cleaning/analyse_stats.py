import os
import pandas as pd
import matplotlib.pyplot as plt

# ==================== Configuration ====================

# Define multipliers for lower and upper IQR bounds
# To **tighten** bounds: decrease multipliers
# To **loosen** bounds: increase multipliers
MULTIPLIERS = {
    'avg_chars_per_line': {
        'lower': 0.4,  # Lower value tightens lower bound
        'upper': 0.15   # Lower value tightens upper bound
    },
    'num_lines': {
        'lower': 0.8,  # Lower value tightens lower bound
        'upper': 0.9   # Lower value tightens upper bound
    }
}

# Columns to apply IQR bounds
COLUMNS_TO_BOUND = ['avg_chars_per_line', 'num_lines']

# ========================================================

# Set folder paths
folder_path = "/home/fivos/Desktop/New Folder/Sxolika/filtered_by_JSON/cleaned_filtered_extracted_txt/"
statistics_folder = os.path.join(folder_path, "statistics")

# Create statistics folder if it doesn't exist
os.makedirs(statistics_folder, exist_ok=True)

# Collect file statistics
file_stats = []
for filename in os.listdir(folder_path):
    if filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                num_lines = len(lines)
                total_chars = sum(len(line.strip()) for line in lines)
                avg_chars_per_line = total_chars / num_lines if num_lines > 0 else 0
                file_stats.append([filename, round(avg_chars_per_line, 1), num_lines, total_chars])
        except Exception as e:
            print(f"Error processing {filename}: {e}")

# Create DataFrame and save
df = pd.DataFrame(file_stats, columns=['filename', 'avg_chars_per_line', 'num_lines', 'total_chars'])
df.to_csv(os.path.join(statistics_folder, 'file_statistics.csv'), index=False)

# ==================== Outlier Detection ====================

# Function to calculate median-based bounds
def calculate_median_bounds(series, lower_multiplier=0.5, upper_multiplier=1.5):
    median = series.quantile(0.5)
    minimum = series.min()
    maximum = series.max()
    
    lower_range = median - minimum
    upper_range = maximum - median
    
    lower_bound = median - (lower_multiplier * lower_range)
    upper_bound = median + (upper_multiplier * upper_range)
    
    return lower_bound, upper_bound

# Calculate bounds for each column using the median-based method
median_bounds = {}
for column in COLUMNS_TO_BOUND:
    multipliers = MULTIPLIERS.get(column, {'lower': 0.5, 'upper': 1.5})  # Adjust default multipliers as needed
    lower, upper = calculate_median_bounds(df[column], multipliers['lower'], multipliers['upper'])
    median_bounds[column] = (lower, upper)

# Initialize a boolean series with False
outlier_condition = pd.Series([False] * len(df))

# Iterate through each specified column to update the condition
for column in COLUMNS_TO_BOUND:
    lower_bound, upper_bound = median_bounds[column]
    
    # Update the condition
    outlier_condition |= (df[column] < lower_bound) | (df[column] > upper_bound)

# Filter the DataFrame based on the aggregated condition
extreme_values_df = df[outlier_condition]

# Plot histograms with Median-Based bounds
for column in COLUMNS_TO_BOUND:
    plt.figure(figsize=(10, 6))
    plt.hist(df[column], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    
    # Plot lower and upper median-based bounds
    plt.axvline(median_bounds[column][0], color='red', linestyle='dashed', linewidth=2, label='Lower Bound')
    plt.axvline(median_bounds[column][1], color='green', linestyle='dashed', linewidth=2, label='Upper Bound')
    
    # Update title to reflect Median-Based bounds
    plt.title(f'Distribution of {column} with Median-Based Bounds')
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.legend()
    
    # Ensure the statistics folder exists
    os.makedirs(statistics_folder, exist_ok=True)
    
    # Save the plot with a descriptive filename
    plt.savefig(os.path.join(statistics_folder, f'{column}_median_bounds.png'))
    plt.close()
    
# Identify outliers for each column using median-based bounds
out_of_bound_dfs = {}
for column in COLUMNS_TO_BOUND:
    lower, upper = median_bounds[column]
    condition = (df[column] < lower) | (df[column] > upper)
    out_of_bound = df[condition][['filename']]
    out_of_bound_dfs[column] = out_of_bound

# Identify all outlier filenames (outliers in all column)
if len(COLUMNS_TO_BOUND) >= 2:
    # Start with the outliers from the first column
    overlapping_outliers = out_of_bound_dfs[COLUMNS_TO_BOUND[0]].copy()
    
    # Iteratively merge with outliers from the remaining columns
    for column in COLUMNS_TO_BOUND[1:]:
        overlapping_outliers = overlapping_outliers.merge(out_of_bound_dfs[column], on='filename', how='inner')
else:
    # If there's only one column, all outliers from that column are considered
    overlapping_outliers = out_of_bound_dfs[COLUMNS_TO_BOUND[0]].copy()

# Extract unique outlier filenames that are outliers in all specified columns
outlier_filenames = overlapping_outliers['filename'].unique()
# Exclude these files from corpus statistics
filtered_df = df[~df['filename'].isin(outlier_filenames)]

# ==================== Corpus Statistics ====================

# Calculate corpus-level stats from filtered_df
average_avg_chars_per_line = filtered_df['avg_chars_per_line'].mean()
average_num_lines = filtered_df['num_lines'].mean()
average_total_chars = filtered_df['total_chars'].mean()

sum_num_lines = filtered_df['num_lines'].sum()
sum_total_chars = filtered_df['total_chars'].sum()

file_count = filtered_df.shape[0]

# Prepare and save corpus_statistics.txt
corpus_stats_content = (
    f"Corpus Statistics\n"
    f"=================\n"
    f"Total Files Processed: {file_count}\n"
    f"Total Number of Lines: {sum_num_lines}\n"
    f"Total Number of Characters: {sum_total_chars}\n\n"
    f"Average Characters per Line: {average_avg_chars_per_line:.2f}\n"
    f"Average Number of Lines per File: {average_num_lines:.2f}\n"
    f"Average Number of Characters per File: {average_total_chars:.2f}\n\n"
    f"Median-Based Multipliers Used for Analysis:\n"
    f"-------------------------------------------\n"
)

# Append multipliers information
for metric, multipliers in MULTIPLIERS.items():
    corpus_stats_content += (
        f"{metric}:\n"
        f"  Lower Multiplier: {multipliers['lower']}\n"
        f"  Upper Multiplier: {multipliers['upper']}\n"
    )

with open(os.path.join(statistics_folder, 'corpus_statistics.txt'), 'w', encoding='utf-8') as stats_file:
    stats_file.write(corpus_stats_content)

# ===========================================================

# Combine all outliers into extreme_values.csv
# Include outliers from either column
all_outliers = df[df['filename'].isin(outlier_filenames)].copy()
all_outliers['extraction_error'] = 1

# Save extreme_values.csv with required columns
columns_to_save = ['filename', 'avg_chars_per_line', 'num_lines', 'extraction_error']
all_outliers.to_csv(os.path.join(statistics_folder, 'extreme_values.csv'), columns=columns_to_save, index=False)

print("Median-Based Bounds and Value Ranges:")
for column, bounds in median_bounds.items():
    min_val = df[column].min()
    max_val = df[column].max()
    print(f"\n{column}:")
    print(f"  Minimum Value: {min_val:.2f}")
    print(f"  Maximum Value: {max_val:.2f}")
    print(f"  Median-Based Lower Bound: {bounds[0]:.2f}")
    print(f"  Median-Based Upper Bound: {bounds[1]:.2f}")