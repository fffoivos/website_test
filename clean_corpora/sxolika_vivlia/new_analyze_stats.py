import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class BoundConfig:
    lower_multiplier: float
    upper_multiplier: float
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None

class TextAnalyzer:
    def __init__(
        self,
        folder_path: str,
        bounds_config: Dict[str, BoundConfig],
        columns_to_bound: List[str] = ['avg_chars_per_line', 'num_lines']
    ):
        self.folder_path = folder_path
        self.statistics_folder = os.path.join(folder_path, "statistics")
        self.bounds_config = bounds_config
        self.columns_to_bound = columns_to_bound
        os.makedirs(self.statistics_folder, exist_ok=True)

    def process_file(self, file_path: str) -> Optional[Dict]:
        """Process a single text file and return its statistics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file.readlines()]
                non_empty_lines = [line for line in lines if line]
                
                if not non_empty_lines:
                    return None
                
                stats = {
                    'filename': os.path.basename(file_path),
                    'num_lines': len(non_empty_lines),
                    'total_chars': sum(len(line) for line in non_empty_lines),
                    'empty_lines': len(lines) - len(non_empty_lines)
                }
                stats['avg_chars_per_line'] = round(stats['total_chars'] / stats['num_lines'], 1)
                return stats
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None

    def calculate_bounds(self, series: pd.Series, config: BoundConfig) -> Dict[str, float]:
        """Calculate both relative and absolute bounds."""
        median = series.median()
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        
        bounds = {
            'relative_lower': median - (config.lower_multiplier * iqr),
            'relative_upper': median + (config.upper_multiplier * iqr),
            'absolute_lower': config.min_threshold if config.min_threshold is not None else float('-inf'),
            'absolute_upper': config.max_threshold if config.max_threshold is not None else float('inf')
        }
        
        # Final bounds are the more restrictive of relative and absolute
        bounds['final_lower'] = max(bounds['relative_lower'], bounds['absolute_lower'])
        bounds['final_upper'] = min(bounds['relative_upper'], bounds['absolute_upper'])
        
        return bounds

    @staticmethod
    def _calculate_tick_spacing(data_range: float, target_ticks: int = 15) -> float:
        """Calculate appropriate tick spacing based on data range."""
        rough_spacing = data_range / target_ticks
        
        # Find the most appropriate round number for spacing
        magnitude = 10 ** np.floor(np.log10(rough_spacing))
        possible_spacings = [magnitude * x for x in [0.1, 0.2, 0.25, 0.5, 1.0, 2.0, 2.5, 5.0]]
        
        return min([x for x in possible_spacings if x >= rough_spacing])

    def _generate_visualizations(self, df: pd.DataFrame, bounds_info: Dict):
        """Generate and save visualization plots with enhanced x-axis detail."""
        for column in self.columns_to_bound:
            if column in bounds_info:
                plt.figure(figsize=(15, 8))
                
                # Create histogram with KDE
                df[column].hist(bins=50, density=True, alpha=0.6, color='skyblue', label='Distribution')
                kde = df[column].plot(kind='kde', color='navy', linewidth=2, label='Density')
                
                bounds = bounds_info[column]
                
                # Calculate x-axis range with padding
                data_min = df[column].min()
                data_max = df[column].max()
                data_range = data_max - data_min
                x_min = max(data_min - (data_range * 0.1), 0)
                x_max = data_max + (data_range * 0.1)
                
                # Set custom tick spacing based on data range
                if column == 'avg_chars_per_line':
                    tick_spacing = self._calculate_tick_spacing(data_range, target_ticks=15)
                    ticks = np.arange(
                        np.floor(x_min / tick_spacing) * tick_spacing,
                        np.ceil(x_max / tick_spacing) * tick_spacing + tick_spacing,
                        tick_spacing
                    )
                else:  # num_lines
                    tick_spacing = max(1, int(data_range / 20))
                    ticks = np.arange(
                        int(np.floor(x_min)),
                        int(np.ceil(x_max)) + tick_spacing,
                        tick_spacing
                    )
                
                plt.xticks(ticks, rotation=45)
                
                # Plot bounds
                bound_lines = []
                bound_labels = []
                
                # Plot relative bounds
                rel_lower = plt.axvline(bounds['relative_lower'], color='blue', linestyle='--', 
                                      alpha=0.7)
                rel_upper = plt.axvline(bounds['relative_upper'], color='blue', linestyle='--', 
                                      alpha=0.7)
                bound_lines.extend([rel_lower, rel_upper])
                bound_labels.extend(['Relative Lower', 'Relative Upper'])
                
                # Plot absolute bounds if they exist
                if bounds['absolute_lower'] != float('-inf'):
                    abs_lower = plt.axvline(bounds['absolute_lower'], color='red', linestyle='-')
                    bound_lines.append(abs_lower)
                    bound_labels.append('Absolute Lower')
                if bounds['absolute_upper'] != float('inf'):
                    abs_upper = plt.axvline(bounds['absolute_upper'], color='red', linestyle='-')
                    bound_lines.append(abs_upper)
                    bound_labels.append('Absolute Upper')
                
                # Plot final bounds
                final_lower = plt.axvline(bounds['final_lower'], color='green', linestyle='-', 
                                        linewidth=2)
                final_upper = plt.axvline(bounds['final_upper'], color='green', linestyle='-', 
                                        linewidth=2)
                bound_lines.extend([final_lower, final_upper])
                bound_labels.extend(['Final Lower', 'Final Upper'])
                
                # Add detailed annotations for bounds
                y_max = plt.gca().get_ylim()[1]
                for bound_type in ['final_lower', 'final_upper']:
                    bound_value = bounds[bound_type]
                    plt.annotate(
                        f'{bound_value:.1f}',
                        xy=(bound_value, y_max * 0.5),
                        xytext=(10, 0),
                        textcoords='offset points',
                        ha='left',
                        va='center',
                        bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                        arrowprops=dict(arrowstyle='->')
                    )
                
                # Customize grid
                plt.grid(True, linestyle='--', alpha=0.7)
                
                # Set labels and title with more detail
                metric_name = 'Characters per Line' if column == 'avg_chars_per_line' else 'Number of Lines'
                plt.title(f'Distribution of {metric_name}\nwith Relative and Absolute Bounds', 
                         pad=20, fontsize=12)
                plt.xlabel(f'{metric_name}\n(Showing {len(df)} files)', labelpad=10)
                plt.ylabel('Density', labelpad=10)
                
                # Add statistics annotation
                stats_text = (
                    f'Mean: {df[column].mean():.1f}\n'
                    f'Median: {df[column].median():.1f}\n'
                    f'Std Dev: {df[column].std():.1f}\n'
                    f'Files within bounds: {len(df[(df[column] >= bounds["final_lower"]) & (df[column] <= bounds["final_upper"])])}'
                )
                plt.annotate(
                    stats_text,
                    xy=(0.02, 0.98),
                    xycoords='axes fraction',
                    bbox=dict(boxstyle='round', fc='white', alpha=0.8),
                    va='top'
                )
                
                # Create custom legend
                plt.legend(
                    [plt.Rectangle((0,0),1,1, fc='skyblue', alpha=0.6)] + bound_lines,
                    ['Distribution'] + bound_labels,
                    bbox_to_anchor=(1.05, 1),
                    loc='upper left'
                )
                
                plt.tight_layout()
                plt.savefig(os.path.join(self.statistics_folder, f'{column}_median_bounds.png'),
                           bbox_inches='tight', dpi=300)
                plt.close()

    def _save_files(self, df: pd.DataFrame, filtered_df: pd.DataFrame, outliers_df: pd.DataFrame):
        """Save files with original naming convention."""
        # Save full statistics
        df.to_csv(os.path.join(self.statistics_folder, 'file_statistics.csv'), index=False)
        
        # Save extreme values (outliers) with specific columns
        columns_to_save = ['filename', 'avg_chars_per_line', 'num_lines', 'extraction_error']
        outliers_df[columns_to_save].to_csv(
            os.path.join(self.statistics_folder, 'extreme_values.csv'), 
            index=False
        )

    def _save_statistics(self, df: pd.DataFrame, filtered_df: pd.DataFrame, 
                        outliers_df: pd.DataFrame, bounds_info: Dict):
        """Save comprehensive statistics about the analysis."""
        stats_content = "Corpus Statistics\n=================\n"
        
        # Add basic statistics
        stats_content += f"Total Files Processed: {len(df)}\n"
        stats_content += f"Files After Filtering: {len(filtered_df)}\n"
        stats_content += f"Outliers Identified: {len(outliers_df)}\n\n"
        
        # Add filtered corpus statistics
        stats_content += "Filtered Corpus Statistics\n"
        stats_content += f"Total Number of Lines: {filtered_df['num_lines'].sum()}\n"
        stats_content += f"Total Number of Characters: {filtered_df['total_chars'].sum()}\n\n"
        stats_content += f"Average Characters per Line: {filtered_df['avg_chars_per_line'].mean():.2f}\n"
        stats_content += f"Average Number of Lines per File: {filtered_df['num_lines'].mean():.2f}\n"
        
        # Add bounds information
        stats_content += "\nBounds Information\n-----------------\n"
        for column, bounds in bounds_info.items():
            stats_content += f"\n{column}:\n"
            stats_content += f"  Relative Bounds: {bounds['relative_lower']:.2f} - {bounds['relative_upper']:.2f}\n"
            if bounds['absolute_lower'] != float('-inf'):
                stats_content += f"  Absolute Lower Threshold: {bounds['absolute_lower']}\n"
            if bounds['absolute_upper'] != float('inf'):
                stats_content += f"  Absolute Upper Threshold: {bounds['absolute_upper']}\n"
            stats_content += f"  Final Bounds: {bounds['final_lower']:.2f} - {bounds['final_upper']:.2f}\n"
        
        with open(os.path.join(self.statistics_folder, 'corpus_statistics.txt'), 'w') as f:
            f.write(stats_content)

    def analyze(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Analyze text files and return both full and filtered DataFrames."""
        # Process files
        file_stats = []
        for filename in os.listdir(self.folder_path):
            if filename.endswith(".txt"):
                stats = self.process_file(os.path.join(self.folder_path, filename))
                if stats:
                    file_stats.append(stats)

        df = pd.DataFrame(file_stats)
        
        # Calculate bounds and identify outliers
        outlier_mask = pd.Series(False, index=df.index)
        bounds_info = {}
        
        for column in self.columns_to_bound:
            if column in df.columns:
                config = self.bounds_config.get(column)
                if config:
                    bounds = self.calculate_bounds(df[column], config)
                    bounds_info[column] = bounds
                    outlier_mask |= (df[column] < bounds['final_lower']) | (df[column] > bounds['final_upper'])

        # Create filtered DataFrame and outliers DataFrame
        filtered_df = df[~outlier_mask].copy()
        outliers_df = df[outlier_mask].copy()
        
        # Add extraction_error column to outliers DataFrame
        outliers_df['extraction_error'] = 1
        
        # Save files
        self._save_files(df, filtered_df, outliers_df)
        
        # Generate visualizations
        self._generate_visualizations(df, bounds_info)
        
        # Save statistics
        self._save_statistics(df, filtered_df, outliers_df, bounds_info)
        
        return filtered_df, outliers_df

# Example usage
if __name__ == "__main__":
    # Define your folder path
    folder_path = "/home/fivos/Desktop/text_sources/sxolika_vivlia/paste_texts/deduplicated_texts/unique/filtered_by_JSON/xondrikos_katharismos_papers/fine_cleaning_v4"
    
    # Configure bounds
    bounds_config = {
        'avg_chars_per_line': BoundConfig(
            lower_multiplier=0.4,
            upper_multiplier=0.6,
            min_threshold=20,  # Minimum reasonable characters per line
            max_threshold=200  # Maximum reasonable characters per line
        ),
        'num_lines': BoundConfig(
            lower_multiplier=0.9,
            upper_multiplier=0.4,
            min_threshold=10   # Minimum reasonable number of lines
        )
    }
    
    # Create analyzer instance and run analysis
    analyzer = TextAnalyzer(
        folder_path=folder_path,
        bounds_config=bounds_config
    )
    
    filtered_df, outliers_df = analyzer.analyze()
    
    print("\nAnalysis complete! Check the 'statistics' folder for detailed results.")
    print(f"Processed {len(filtered_df) + len(outliers_df)} files total")
    print(f"Kept {len(filtered_df)} files within bounds")
    print(f"Identified {len(outliers_df)} outliers")