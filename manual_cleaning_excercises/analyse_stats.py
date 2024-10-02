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
        'upper': 1.4   # Lower value tightens upper bound
    },
    'num_lines': {
        'lower': 0.6,  # Lower value tightens lower bound
        'upper': 1.8   # Lower value tightens upper bound
    }
}

# Columns to apply IQR bounds
COLUMNS_TO_BOUND = ['avg_chars_per_line', 'num_lines']

# ========================================================

# Set folder paths
folder_path = "/home/fivos/Desktop/cleaned_filtered_extracted_sxolika/filtered_by_JSON"
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
                total_chars = sum(len(line) for line in lines)
                avg_chars_per_line = total_chars / num_lines if num_lines > 0 else 0
                file_stats.append([filename, round(avg_chars_per_line, 1), num_lines, total_chars])
        except Exception as e:
            print(f"Error processing {filename}: {e}")

# Create DataFrame and save
df = pd.DataFrame(file_stats, columns=['filename', 'avg_chars_per_line', 'num_lines', 'total_chars'])
df.to_csv(os.path.join(statistics_folder, 'file_statistics.csv'), index=False)

# ==================== Outlier Detection ====================

# Function to calculate IQR bounds
def calculate_iqr_bounds(series, lower_multiplier=1.5, upper_multiplier=1.5):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - lower_multiplier * IQR
    upper_bound = Q3 + upper_multiplier * IQR
    return lower_bound, upper_bound

# Calculate bounds for each column
iqr_bounds = {}
for column in COLUMNS_TO_BOUND:
    multipliers = MULTIPLIERS.get(column, {'lower': 1.5, 'upper': 1.5})
    lower, upper = calculate_iqr_bounds(df[column], multipliers['lower'], multipliers['upper'])
    iqr_bounds[column] = (lower, upper)

# Display IQR bounds and extreme value ranges
print("IQR-based bounds and Extreme Value Ranges:")
for column, bounds in iqr_bounds.items():
    # Identify outliers for the current column
    outliers = df[(df[column] < bounds[0]) | (df[column] > bounds[1])][column]
    if not outliers.empty:
        min_outlier = outliers.min()
        max_outlier = outliers.max()
        print(f"  {column}: {bounds[0]:.2f} - {bounds[1]:.2f}")
        print(f"    Extreme values: {min_outlier:.2f} - {max_outlier:.2f}")
    else:
        print(f"  {column}: {bounds[0]:.2f} - {bounds[1]:.2f}")
        print(f"    Extreme values: None")

# Plot histograms with IQR bounds
for column in COLUMNS_TO_BOUND:
    plt.figure(figsize=(10, 6))
    plt.hist(df[column], bins=30, alpha=0.7, color='b', edgecolor='black')
    plt.axvline(iqr_bounds[column][0], color='r', linestyle='dashed', linewidth=2, label='Lower Bound')
    plt.axvline(iqr_bounds[column][1], color='g', linestyle='dashed', linewidth=2, label='Upper Bound')
    plt.title(f'Distribution of {column} with IQR Bounds')
    plt.xlabel(column)
    plt.ylabel('Frequency')
    plt.legend()
    plt.savefig(os.path.join(statistics_folder, f'{column}_iqr_bounds.png'))
    plt.close()

# Identify outliers for each column
out_of_bound_dfs = {}
for column in COLUMNS_TO_BOUND:
    lower, upper = iqr_bounds[column]
    condition = (df[column] < lower) | (df[column] > upper)
    out_of_bound = df[condition][['filename']]
    out_of_bound_dfs[column] = out_of_bound

# Identify all outlier filenames (outliers in either column)
outlier_filenames = pd.concat(out_of_bound_dfs.values())['filename'].unique()

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
    f"IQR Multipliers Used for Analysis:\n"
    f"-----------------------------------\n"
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

# Print outliers per column
for column in COLUMNS_TO_BOUND:
    print(f"\nFiles out of bounds for {column}:")
    out_of_bound = out_of_bound_dfs[column][['filename']]
    if not out_of_bound.empty:
        print(out_of_bound.to_string(index=False))
    else:
        print("  None")

# Print files outliers in both columns
print("\nFiles out of bounds for both average characters per line and number of lines:")
# To find files that are outliers in both columns, intersect the outlier sets
outliers_avg = set(out_of_bound_dfs['avg_chars_per_line']['filename'])
outliers_num = set(out_of_bound_dfs['num_lines']['filename'])
outliers_both = outliers_avg.intersection(outliers_num)

if outliers_both:
    outlier_both_details = df[df['filename'].isin(outliers_both)][['filename', 'avg_chars_per_line', 'num_lines']]
    print(outlier_both_details.to_string(index=False))
else:
    print("  None")
