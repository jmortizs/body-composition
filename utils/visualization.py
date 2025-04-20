import matplotlib.pyplot as plt
import seaborn as sns
from typing import Literal
import polars as pl
import numpy as np
from scipy import stats

def plot_variable_comparison(
    df,
    x_var: Literal["weight", "skeletal_muscle_mass", "body_fat_mass", "basal_metabolic_rate"],
    y_var: Literal["weight", "skeletal_muscle_mass", "body_fat_mass", "basal_metabolic_rate"],
    figsize: tuple[int, int] = (10, 6),
    title: str | None = None,
    x_label: str | None = None,
    y_label: str | None = None,
) -> None:
    """
    Create a scatter plot comparing two variables from the body composition data,
    with elapse_days as the hue and a linear regression line.

    Args:
        df: DataFrame containing body composition data
        x_var: Variable to plot on x-axis
        y_var: Variable to plot on y-axis
        figsize: Figure size as (width, height) in inches
        title: Optional title for the plot. If None, a default title will be generated
        x_label: Optional label for the x-axis. If None, the variable name will be used.
        y_label: Optional label for the y-axis. If None, the variable name will be used.

    Returns:
        None
    """
    # Set the style
    sns.set_style("whitegrid")

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=figsize)

    # Create the scatter plot without legend
    scatter = sns.scatterplot(
        data=df,
        x=x_var,
        y=y_var,
        hue="elapse_days",
        palette="viridis",
        alpha=0.7,
        ax=ax,
        legend=False
    )

    # Calculate linear regression
    x_data = df[x_var].to_numpy()
    y_data = df[y_var].to_numpy()
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)

    # Create regression line
    x_line = np.linspace(x_data.min(), x_data.max(), 100)
    y_line = slope * x_line + intercept

    # Plot regression line with dashed style and alpha
    ax.plot(x_line, y_line, 'r--', alpha=0.8, label=f'y = {slope:.2f}x + {intercept:.2f}')

    # Get the colorbar from the scatter plot
    norm = plt.Normalize(df["elapse_days"].min(), df["elapse_days"].max())
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
    sm.set_array([])

    # Add the colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Days Elapsed")

    # Set title if provided, otherwise generate one
    if title is None:
        title = f"{y_var} vs {x_var} by Days Elapsed"
    plt.title(title, pad=20)

    # Add labels
    plt.xlabel(x_label if x_label else x_var.replace("_", " ").title())
    plt.ylabel(y_label if y_label else y_var.replace("_", " ").title())

    # Add legend for regression line only
    ax.legend()

    # Add grid
    plt.grid(True, alpha=0.3)

    # Adjust layout
    plt.tight_layout()

    # Show the plot
    plt.show()
