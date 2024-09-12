import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import rgb2hex

# Read the combined CSV file
df = pd.read_csv(
    "/home/fivos/Projects/GlossAPI/manipulate_data/text_with_pc_annotations_and_originals.csv",
    sep=",",
    engine="python",
)

print(f"Total number of rows in the dataset: {len(df)}")

# Extract columns for PCA components
x1 = df["PC4"]
x2 = df["PC5"]

# Get unique values from Ποικιλία column
unique_varieties = df["Ποικιλία"].fillna("NaN").unique()  # Handle NaN values explicitly

# Create a color map
color_map = {}
cmap = plt.cm.get_cmap('tab20')  # Colormap with enough distinct colors
for i, variety in enumerate(unique_varieties):
    color_map[variety] = rgb2hex(cmap(i / len(unique_varieties)))

# Create a single figure
plt.figure(figsize=(12, 8))

# Create scatter plot
for variety in unique_varieties:
    mask = df["Ποικιλία"].fillna("NaN") == variety  # Ensure NaN values are accounted for
    plt.scatter(x1[mask], x2[mask], c=color_map[variety], alpha=0.7, label=variety, s=30)
    print(f"Number of points for {variety}: {sum(mask)}")

plt.xlabel("PC1")
plt.ylabel("PC2")
plt.title("PC1 vs PC2 colored by Ποικιλία")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# Adjust layout to prevent overlapping
plt.tight_layout()

# Show the plot
plt.show()

# Print unique values in the Ποικιλία column
print("\nUnique values in Ποικιλία column:")
print(df["Ποικιλία"].value_counts(dropna=False))
