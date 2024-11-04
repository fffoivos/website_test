import pandas as pd
import matplotlib.pyplot as plt
import random

# Read the combined CSV file
df = pd.read_csv(
    "/home/fivos/Projects/GlossAPI/manipulate_data/combined_draw_with_normalized_variety.csv",
    sep=",",
    engine="python",
)

# Extract columns '1', '2', and '3'
x1 = df["1"]
x2 = df["2"]
x3 = df["3"]

# Create a color map
color_map = {"Δημοτική": "blue", "Καθαρεύουσα": "red", "ΚΝΕ": "green"}

# Create a figure with three subplots
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))


# Function to create scatter plot
def create_scatter(ax, x, y, xlabel, ylabel):
    for variety in color_map:
        mask = df["ΠΟΙΚΙΛΙΑ_NORMALIZED"] == variety
        ax.scatter(x[mask], y[mask], c=color_map[variety], alpha=0.5, label=variety)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()


# Create the three scatter plots
create_scatter(ax1, x1, x2, "Column 1", "Column 2")
create_scatter(ax2, x1, x3, "Column 1", "Column 3")
create_scatter(ax3, x3, x2, "Column 2", "Column 3")

# Set titles for each subplot
ax1.set_title("Column 1 vs Column 2")
ax2.set_title("Column 1 vs Column 3")
ax3.set_title("Column 2 vs Column 3")

# Adjust layout to prevent overlapping
plt.tight_layout()

# Show the plot
plt.show()
