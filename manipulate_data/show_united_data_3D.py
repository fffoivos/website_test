import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import random

# Read the combined CSV file
df = pd.read_csv('/home/fivos/Projects/GlossAPI/glossAPI/data/text_with_pca_annotations.csv', sep=',', engine='python')

# Extract columns '1', '2', and '3'
x = df['PC1']
y = df['PC2']
z = df['PC3']

# Create a color map
color_map = {'Δημοτική': 'blue', 'Καθαρεύουσα': 'red', 'ΚΝΕ': 'green'}

# Create the 3D scatter plot
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

for variety in color_map:
    mask = df['ΠΟΙΚΙΛΙΑ_NORMALIZED'] == variety
    ax.scatter(x[mask], y[mask], z[mask], c=color_map[variety], alpha=0.5, label=variety)

# Set labels and title
ax.set_xlabel('x - 1')
ax.set_ylabel('y - 2')
ax.set_zlabel('z - 3')
ax.set_title('3D Scatter Plot of Columns 1, 2, and 3 (Colored by Variety)')

# Add legend
ax.legend()

# Randomly select some points to annotate
num_annotations = 0  # You can adjust this number
indices = random.sample(range(len(df)), num_annotations)

# Add annotations for the selected points
for i in indices:
    ax.text(x.iloc[i], y.iloc[i], z.iloc[i], f"{df['text'].iloc[i][:30]}",
            fontsize=8)

# Adjust layout to prevent clipping of annotations
plt.tight_layout()

# Show the plot
plt.show()