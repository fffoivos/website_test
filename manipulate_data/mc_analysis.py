import pandas as pd
import prince
import matplotlib.pyplot as plt
import seaborn as sns

# Load your data
data = pd.read_csv("/home/fivos/Projects/GlossAPI/manipulate_data/text_with_pc_annotations_and_originals.csv", sep=",", engine="python")

# Select only the categorical columns for MCA
categorical_columns = [ 'Διάλεκτος', 'Κοινωνιόλεκτος', 'Jargon', 'Ποικιλία', 'Ιστορική.Περίοδος']
mca_data = data[categorical_columns]

# Initialize and fit the MCA model
mca = prince.MCA(n_components=2, n_iter=3, random_state=42)
mca_results = mca.fit(mca_data)

# Get the coordinates
coord = mca.column_coordinates(mca_data)
contrib = mca.column_contributions(mca_data)

# Plot the results
plt.figure(figsize=(12, 10))
sns.scatterplot(data=coord, x=0, y=1, hue=coord.index.get_level_values(0), 
                size=contrib[0], sizes=(20, 200), legend='full')

plt.title("MCA - Variable Categories")
plt.xlabel(f"Dimension 1 ({mca.explained_inertia_ratio_[0]:.2%})")
plt.ylabel(f"Dimension 2 ({mca.explained_inertia_ratio_[1]:.2%})")
plt.tight_layout()
plt.savefig('mca_coordinates.png')
plt.show()

# Print eigenvalues and explained inertia
print("Eigenvalues:", mca.eigenvalues_)
print("Total inertia:", mca.total_inertia_)
print("Explained inertia ratio:", mca.explained_inertia_ratio_)

# Access the coordinates
row_coordinates = mca.row_coordinates(mca_data)
column_coordinates = mca.column_coordinates(mca_data)

print("\nFirst few row coordinates:")
print(row_coordinates.head())

print("\nFirst few column coordinates:")
print(column_coordinates.head())