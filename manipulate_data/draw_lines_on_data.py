

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
# Read the combined CSV file
df = pd.read_csv(
    "/home/fivos/Projects/GlossAPI/manipulate_data/combined_draw_with_normalized_variety.csv",
    sep=",",
    engine="python",
)



# Extract columns '2' and '3'
x2 = df["2"]
x3 = df["3"]

# Create a color map
color_map = {"Δημοτική": "blue", "Καθαρεύουσα": "red", "ΚΝΕ": "green"}

# Create a single figure
fig, ax = plt.subplots(figsize=(12, 8))

# Function to create scatter plot
def create_scatter(ax, x, y, xlabel, ylabel):
    for variety in color_map:
        mask = df["ΠΟΙΚΙΛΙΑ_NORMALIZED"] == variety
        ax.scatter(x[mask], y[mask], c=color_map[variety], alpha=0.5, label=variety)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()

# Create the scatter plot
create_scatter(ax, x3, x2, "Column 3", "Column 2")

# Set title for the plot
ax.set_title("Column 3 vs Column 2")

# Adjust layout
plt.tight_layout()

# Interactive line drawing
lines = []
line_artists = []

def onclick(event):
    if event.inaxes != ax:
        return
    lines.append((event.xdata, event.ydata))
    if len(lines) % 2 == 0:
        x1, y1 = lines[-2]
        x2, y2 = lines[-1]
        line, = ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)
        line_artists.append(line)
    fig.canvas.draw()

def get_equations(event):
    for i in range(0, len(lines), 2):
        x1, y1 = lines[i]
        x2, y2 = lines[i+1]
        m = (y2 - y1) / (x2 - x1)
        b = y1 - m * x1
        print(f"Line {i//2 + 1}: y = {m:.2f}x + {b:.2f}")

fig.canvas.mpl_connect('button_press_event', onclick)

axbutton = plt.axes([0.81, 0.05, 0.1, 0.075])
button = Button(axbutton, 'Get Equations')
button.on_clicked(get_equations)

plt.show()