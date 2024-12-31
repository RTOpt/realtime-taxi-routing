import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import seaborn as sns
from src.utilities.tools import create_solution_description, merge_algorithms_param, add_data_labels


def offline_plot(data_path, metrics):
    # Read the dataset
    df = pd.read_csv(data_path)

    # Group by 'Time window (min)', 'Objective type' and calculate the mean for the required columns
    grouped = df.groupby(['Time window (min)', 'Objective type'])[metrics].mean().reset_index()

    # Define metrics and titles
    colors = sns.color_palette("gist_earth", n_colors=3)

    # Create the plot
    fig, axes = plt.subplots(3, 1, figsize=(6, 8), sharex=True)

    for i, metric in enumerate(metrics):
        ax = axes[i]
        # Pivot data for easy plotting
        pivot_data = grouped.pivot(index='Time window (min)', columns='Objective type', values=metric)
        pivot_data.columns = [col.replace('_', ' ').capitalize() for col in pivot_data.columns]
        # Plot each Objective_type
        pivot_data.plot(kind='bar', ax=ax, color=colors[:len(pivot_data.columns)], alpha=0.8,  edgecolor='darkslategray')

        # Adjust x-tick labels
        ax.tick_params(axis='x', labelrotation=0)

        ax.set_xlabel('Time Window (min)', fontsize=10, fontweight='bold')
        ax.set_ylabel(metric, fontsize=10, fontweight='bold')
        ax.grid(axis='y', linestyle='dotted', color='darkgray', alpha=0.7)

        # Calculate y-axis limits based on data
        data_min = pivot_data.min().min()
        data_max = pivot_data.max().max()
        step_size = round((data_max - data_min)/3,0)
        y_min = max(0,data_min - 1.5*step_size)
        y_max = data_max + 0.5*step_size
        ax.set_ylim(y_min, y_max)
        ax.minorticks_off()
        add_data_labels(ax, metric, y_min, y_max, 0.15)

        # Add legend only for the first subplot
        if i == 0:
            ax.legend(title='Objective Type', bbox_to_anchor=(0.5, 1.25), loc='upper center', ncol=3, fontsize=9,
                      title_fontproperties={'weight': 'bold', 'size': 9}, edgecolor='darkslategray')
        else:
            ax.legend_.remove()  # Remove legend for other subplots

    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.05)

    # Save the plot
    figure_path = os.path.join(os.path.dirname(data_path), 'offline_plot.png')
    plt.savefig(figure_path, dpi=300, bbox_inches='tight')

    # Show the plot
    plt.show(block=False)  # Show plot without blocking the script
    plt.pause(2)  # Pause for 2 seconds
    plt.close()

def compare_algorithm_plot(data_path, metrics):
    # Read the dataset
    df = pd.read_csv(data_path)

    # Ensure that 'Solution Description' is created correctly
    df['Solution Description'] = df.apply(create_solution_description, axis=1)
    df['Algorithms'] = df.apply(merge_algorithms_param, axis=1)



    # Group by 'Solution Description' and 'Destroy Method' and calculate the mean for the required columns
    grouped = df.groupby(['Solution Description', 'Algorithms', 'Objective type'])[metrics].mean().reset_index()

    # Get unique solution descriptions and algorithms
    solution_descriptions = grouped['Solution Description'].unique()
    algorithms = grouped['Algorithms'].unique()
    objective_types = grouped['Objective type'].unique()

    # Define metrics and colors
    colors = sns.color_palette("gist_earth", n_colors=len(algorithms))

    # Determine the number of Objective Types
    num_objectives = len(objective_types)
    ncols = num_objectives if num_objectives > 1 else 1
    nrows = len(metrics)

    # Define figure size
    # Width scales with number of Objective_types, height scales with number of metrics
    fig_width = 1.2 * len(solution_descriptions) * ncols + 0.7 * ncols
    fig_height = len(metrics) * 2.4 + 0.7
    fig, axes = plt.subplots(nrows, ncols, figsize=(fig_width, fig_height), sharex=True, sharey='row')

    # If there's only one row or column, make sure axes is a 2D array for consistent indexing
    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = np.array([axes])
    elif ncols == 1:
        axes = axes.reshape(-1, 1)

    # Iterate over each metric and Objective_type to create subplots
    for i, metric in enumerate(metrics):
        # Initialize variables to determine y-limits for the entire row
        row_data_min = []
        row_data_max = []

        # First pass to collect data_min and data_max for all objective types in this row
        for j, obj_type in enumerate(objective_types):
            # Filter data for the current Objective_type and metric
            data = grouped[(grouped['Objective type'] == obj_type)][metric]
            row_data_min.append(data.min())
            row_data_max.append(data.max())

        # Calculate overall min and max for the row
        combined_min = min(row_data_min)
        combined_max = max(row_data_max)

        # Determine step size based on combined data
        step_size = max(round((combined_max - combined_min) / 3, 1), 0.2)

        # Calculate y_min and y_max based on metric
        if metric == 'Competitive Ratio':
            if combined_max > 1:
                y_min = max(combined_min - step_size, 1)
                y_max = combined_max + step_size
            else:
                y_min = max(0, combined_min - step_size)
                y_max = min(combined_max + step_size, 1)
            # Format y-axis labels for Competitive Ratio
            y_formatter = ticker.FormatStrFormatter('%.1f')
        else:
            y_min = max(0, combined_min - 0.5 * step_size)
            y_max = combined_max + 0.5 * step_size
            y_formatter = None  # Default formatter

        for j, obj_type in enumerate(objective_types):
            ax = axes[i, j]

            # Filter data for the current Objective_type
            data = grouped[grouped['Objective type'] == obj_type]

            # Pivot data for easy plotting
            pivot_data = data.pivot(index='Solution Description', columns='Algorithms', values=metric)

            # Plot each metric as a bar plot
            pivot_data.plot(kind='bar', ax=ax, color=colors, alpha=0.8, edgecolor='darkslategray')



            # Set labels and title
            if j > 0:
                ax.tick_params(axis='y', which='major', length=0,  labelleft=False)
            if i < nrows-1:
                ax.tick_params(axis='x', which='major', length=0,  labelleft=False)
            if i==nrows-1:
                ax.set_xlabel('Solution Modes', fontsize=10, fontweight='bold')
                ax.tick_params(axis='x', labelrotation=10)

            if j==0:
                ax.set_ylabel(metric.replace('_', ' ').capitalize(), fontsize=10, fontweight='bold')
            ax.grid(axis='y', linestyle='dotted', color='darkgray', alpha=0.7)

            ax.set_ylim(y_min, y_max)
            if y_formatter:
                ax.yaxis.set_major_formatter(y_formatter)
            add_data_labels(ax, metric, y_min, y_max, 0.15)

            # Customize y-axis limits and legend
            if i == 0 and j == 0:
                ax.legend(title='Algorithms', fontsize=9, labelspacing=0.2, title_fontproperties={'weight': 'bold', 'size': 9}, edgecolor='darkslategray')
            else:
                ax.legend().remove()
            # Set title for each Objective_type column
            if num_objectives > 1 and i == 0:
                ax.set_title(f'Obj: {obj_type.replace('_', ' ').capitalize()}', fontsize=10, fontweight='bold')
            ax.minorticks_off()



    # Adjust layout for better spacing
    plt.tight_layout()
    plt.subplots_adjust(hspace=0, wspace=0)

    # Extract the base name from data_path and construct the plot name
    base_filename = os.path.basename(data_path)  # e.g., "TP2_simulation_results.csv"
    # Assuming the prefix is before the first underscore
    plot_prefix = base_filename.split('_')[0]  # e.g., "TP2"

    # Construct the plot filename
    plot_filename = f"{plot_prefix}_plot_{len(metrics)}.png"

    # Save the plot to the same directory as the data file
    figure_path = os.path.join(os.path.dirname(data_path), plot_filename)
    # Display the plot

    plt.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.show(block=False)  # Show plot without blocking the script
    plt.pause(2)  # Pause for 2 seconds
    plt.close()

def compare_timeWindow_plot(data_path, metrics):
    # Read the dataset
    df = pd.read_csv(data_path)

    # Ensure that 'Solution Description' and 'Algorithms' are created correctly
    df['Solution Description'] = df.apply(create_solution_description, axis=1)
    df['Algorithms'] = df.apply(merge_algorithms_param, axis=1)

    # Group by 'Solution Description', 'Algorithms', 'Objective type', and 'Time window (min)' and calculate the mean for the required columns
    grouped = df.groupby(['Solution Description', 'Algorithms', 'Objective type', 'Time window (min)'])[
        metrics].mean().reset_index()

    # Get unique values
    solution_descriptions = grouped['Solution Description'].unique()
    algorithms = grouped['Algorithms'].unique()
    objective_types = grouped['Objective type'].unique()
    time_windows = sorted(grouped['Time window (min)'].unique())

    # Define colors
    colors = sns.color_palette("gist_earth", n_colors=len(algorithms))

    # Iterate over each metric to create separate plots
    for metric in metrics:
        # Determine subplot grid based on number of time windows and objective types
        nrows = len(time_windows)
        ncols = len(objective_types) if len(objective_types) > 1 else 1

        # Define figure size
        fig_width = 1.2 * len(solution_descriptions) * ncols + 0.7 * ncols
        fig_height = len(time_windows) * 2.5 + 1
        fig, axes = plt.subplots(nrows, ncols, figsize=(fig_width, fig_height), sharex=True)

        # Ensure axes is a 2D array for consistent indexing
        if nrows == 1 and ncols == 1:
            axes = np.array([[axes]])
        elif nrows == 1:
            axes = np.array([axes])
        elif ncols == 1:
            axes = axes.reshape(-1, 1)
        y_limits_per_col = []
        # First pass: Determine y-axis limits for each column
        for j, obj_type in enumerate(objective_types):
            # Filter data for the current Objective_type
            data_obj = grouped[grouped['Objective type'] == obj_type]

            # Compute the global min and max for the current metric and objective type
            data_max = data_obj[metric].max()
            data_min = data_obj[metric].min()
            step_size = max(round((data_max - data_min) / 3, 1), 0.1)
            if metric == 'Competitive Ratio':
                if data_max > 1:
                    y_min = max(data_min - step_size, 1)
                    y_max = data_max + step_size
                else:
                    y_min = max(0, data_min - step_size)
                    y_max = min(data_max + step_size, 1)
            else:
                y_min = max(0, data_min - 1.5 * step_size)
                y_max = data_max + 0.5 * step_size

            y_limits_per_col.append((y_min, y_max))

        # Iterate over each time window and objective type to create subplots
        for i, obj_type in enumerate(objective_types):
            for j, tw in enumerate(time_windows):
                ax = axes[i, j] if ncols > 1 else axes[i, 0]

                # Filter data for the current Objective_type and Time window
                data = grouped[
                    (grouped['Objective type'] == obj_type) &
                    (grouped['Time window (min)'] == tw)
                    ]

                # Pivot data for easy plotting
                pivot_data = data.pivot(index='Solution Description', columns='Algorithms', values=metric)

                # Plot each metric as a bar plot
                pivot_data.plot(kind='bar', ax=ax, color=colors, alpha=0.8, edgecolor='darkslategray')

                # Add data labels on the bars
                # Apply y-axis limits based on precomputed values
                y_min, y_max = y_limits_per_col[i]
                ax.set_ylim(y_min, y_max)
                add_data_labels(ax, metric, y_min, y_max, 0.15)

                # Set labels and title
                if j > 0:
                    ax.tick_params(axis='y', which='major', length=0, labelleft=False)
                if i < nrows - 1:
                    ax.tick_params(axis='x', which='major', length=0, labelleft=False)
                if i == nrows - 1:
                    ax.set_xlabel('Solution Modes', fontsize=10, fontweight='bold')
                    ax.tick_params(axis='x', labelrotation=10)

                if j == 0:
                    ax.set_ylabel(f'Obj: {obj_type.replace("_", " ").capitalize()}', fontsize=10,
                                  fontweight='bold')
                ax.grid(axis='y', linestyle='dotted', color='darkgray', alpha=0.7)




                # Customize legend
                if i == 0 and j == 0:
                    ax.legend(title='Algorithms', fontsize=9, labelspacing=0.2,
                              title_fontproperties={'weight': 'bold', 'size': 9},
                              edgecolor='darkslategray')
                else:
                    ax.legend().remove()

                # Set title for each Objective_type column
                if len(objective_types) > 1 and i == 0:
                    ax.set_title(f'Time Window: {tw} min', fontsize=10, fontweight='bold')
                ax.minorticks_off()

        # Adjust layout for better spacing
        fig.suptitle(f'{metric}', fontsize=12, fontweight='bold', y=0.98)
        plt.tight_layout()
        plt.subplots_adjust(hspace=0, wspace=0)

        # Extract the base name from data_path and construct the plot name
        base_filename = os.path.basename(data_path)  # e.g., "TP2_simulation_results.csv"
        # Assuming the prefix is before the first underscore
        plot_prefix = base_filename.split('_')[0]  # e.g., "TP2"

        # Construct the plot filename with metric name
        plot_filename = f"{plot_prefix}_{metric}_tw_plot.png"

        # Save the plot to the same directory as the data file
        figure_path = os.path.join(os.path.dirname(data_path), plot_filename)

        # Save and show the plot
        plt.savefig(figure_path, dpi=300, bbox_inches='tight')
        plt.show(block=False)  # Show plot without blocking the script
        plt.pause(2)  # Pause for 2 seconds
        plt.close()


def number_scenarios(data_path, metrics):
    # Read the dataset
    df = pd.read_csv(data_path)

    # Ensure that 'Solution Description' is created correctly
    df['Algorithms'] = df.apply(merge_algorithms_param, axis=1)



    # Group by 'Solution Description' and 'Destroy Method' and calculate the mean for the required columns
    grouped = df.groupby(['Algorithms', '# Scenarios'])[metrics].mean().reset_index()

    # Get unique solution descriptions and algorithms
    algorithms = grouped['Algorithms'].unique()
    scenarios = grouped['# Scenarios'].unique()

    # Define metrics and colors
    colors = sns.color_palette("gist_earth", n_colors=len(algorithms))


    # Define figure size
    fig, ax = plt.subplots(figsize=(6,3.5))

    # Pivot data for easy plotting
    pivot_data = grouped.pivot(index='# Scenarios', columns='Algorithms', values=metrics[0])

    # Plot each metric as a bar plot
    pivot_data.plot(kind='line', ax=ax, color=colors, marker='o', linewidth=2)

    ax.legend(title='Algorithms', fontsize=9, labelspacing=0.2, title_fontproperties={'weight': 'bold', 'size': 9},
              edgecolor='darkslategray')

    ax.grid(axis='both', linestyle='dotted', color='darkgray', alpha=0.7)
    ax.set_xlabel("# Scenarios", fontsize=10, fontweight='bold')
    ax.set_xticks(scenarios)
    ax.tick_params(axis='x')

    ax.set_ylabel(metrics[0], fontsize=10, fontweight='bold')

    # Calculate y-axis limits based on data
    data_min = pivot_data.min().min()
    data_max = pivot_data.max().max()
    step_size = round((data_max - data_min) / 3, 0)
    y_min = max(0, data_min - 0.5 * step_size)
    y_max = data_max + 0.5 * step_size
    ax.set_ylim(y_min, y_max)



    # Adjust layout for better spacing
    plt.tight_layout()
    plt.subplots_adjust(hspace=0, wspace=0)

    # Extract the base name from data_path and construct the plot name
    base_filename = os.path.basename(data_path)  # e.g., "TP2_simulation_results.csv"
    # Assuming the prefix is before the first underscore
    plot_prefix = base_filename.split('_')[0]  # e.g., "TP2"

    # Construct the plot filename
    plot_filename = f"{plot_prefix}_plot_{len(metrics)}.png"

    # Save the plot to the same directory as the data file
    figure_path = os.path.join(os.path.dirname(data_path), plot_filename)
    # Display the plot

    plt.savefig(figure_path, dpi=300, bbox_inches='tight')
    plt.show(block=False)  # Show plot without blocking the script
    plt.pause(2)  # Pause for 2 seconds
    plt.close()
