from typing import Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
import seaborn as sns
from scipy import stats


def plot_variable_comparison(
    df,
    x_var: Literal["weight", "muscle_mass", "body_fat_mass", "basal_metabolic_rate"],
    y_var: Literal["weight", "muscle_mass", "body_fat_mass", "basal_metabolic_rate"],
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
    # ----- Configuration -----
    plt.style.use('dark_background')
    sns.set_style("darkgrid")

    text_color = '#f0f5fa'
    plt.rcParams.update({
        'text.color': text_color,
        'axes.labelcolor': text_color,
        'xtick.color': text_color,
        'ytick.color': text_color
    })

    # ----- Setup -----
    fig, ax = plt.subplots(figsize=figsize)
    background_color = '#1a1a1a'
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(background_color)

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
    ax.plot(x_line, y_line, color='#eb3f7b', linestyle='--', alpha=0.85, label=f'trend: {slope:.2f}')

    # Get the colorbar from the scatter plot
    norm = plt.Normalize(df["elapse_days"].min(), df["elapse_days"].max())
    sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
    sm.set_array([])

    # Add the colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label("Days Elapsed", color=text_color)
    cbar.ax.yaxis.set_tick_params(color=text_color)

    # Set title if provided, otherwise generate one
    if title is None:
        title = f"{y_var.replace('_', ' ').title()} vs {x_var.replace('_', ' ').title()}\nR-squared: {r_value:.2f}"
    plt.title(title, pad=20, color=text_color)

    # Add labels
    plt.xlabel(x_label if x_label else x_var.replace("_", " ").title(), color=text_color)
    plt.ylabel(y_label if y_label else y_var.replace("_", " ").title(), color=text_color)

    # Add legend for regression line only
    ax.legend(fontsize=10, facecolor=background_color, edgecolor=text_color)

    # Add grid
    plt.grid(True, alpha=0.1, color=text_color, linestyle='--')

    # Remove top and right spines
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(text_color)

    # Adjust layout
    plt.tight_layout()

    # Show the plot
    plt.show()



def plot_monthly_progress(
    df: pl.DataFrame,
    metric: Literal["weight", "muscle_mass", "body_fat_mass"],
    figsize: tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    y_label: Optional[str] = None,
    positive_change: bool = True,
) -> None:
    """
    Create a line plot showing monthly progress for a given metric, including standard deviation bands
    and month-to-month variations.

    Args:
        df: Polars DataFrame containing monthly statistics data.
        metric: The metric to plot (weight, muscle_mass, or body_fat_mass).
        figsize: Size of the plot as (width, height) in inches.
        title: Optional custom title for the plot.
        y_label: Optional label for the y-axis.

    Returns:
        None
    """
    # ----- Configuration -----
    plt.style.use('dark_background')
    sns.set_style("darkgrid")

    text_color = '#f0f5fa'
    plt.rcParams.update({
        'text.color': text_color,
        'axes.labelcolor': text_color,
        'xtick.color': text_color,
        'ytick.color': text_color
    })

    # ----- Setup -----
    fig, ax = plt.subplots(figsize=figsize)
    background_color = '#1a1a1a'
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(background_color)

    mean_col = f"{metric}_mean"
    std_col = f"{metric}_std_dev"
    variation_col = f"{metric}_variation"

    months = df.get_column("month").to_list()
    means = df.get_column(mean_col).to_numpy()
    stds = df.get_column(std_col).to_numpy()
    variations = df.get_column(variation_col).to_numpy()

    # Handle edge cases
    if not months or means.size == 0:
        raise ValueError("DataFrame is empty or missing required columns.")

    first_value, last_value = means[0], means[-1]
    total_variation = last_value - first_value
    total_variation_percent = (total_variation / first_value) * 100 if first_value else 0

    # ----- Main Plot -----
    main_color = '#00bfff'
    ax.plot(
        months,
        means,
        marker='o',
        linestyle='-',
        linewidth=2,
        markersize=8,
        color=main_color,
        markerfacecolor='#1a1a1a',
        markeredgecolor=main_color,
        label=f'{metric.replace("_", " ").title()}'
    )

    ax.fill_between(
        months,
        means - stds,
        means + stds,
        alpha=0.15,
        color=main_color,
        label=None
    )

    # ----- Annotations -----
    for i, (x, y, var) in enumerate(zip(months, means, variations)):
        if i == 0 or np.isnan(var):
            continue
        ax.annotate(
            f"{var:+.2f}",
            (x, y),
            xytext=(0, 10),
            textcoords='offset points',
            ha='center',
            fontsize=10,
            color= '#4cd137' if (positive_change and var > 0) or (not positive_change and var < 0) else '#ff6b6b'
        )

    # ----- Labels and Aesthetics -----
    auto_title = (
        f"{metric.replace('_', ' ').title()} Progress\n"
        f"Total Change: {total_variation:+.2f} ({total_variation_percent:+.1f}%)"
    )
    ax.set_title(title or auto_title, fontsize=14, pad=20)

    ax.set_ylabel(y_label or metric.replace("_", " ").title(), fontsize=12)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(text_color)

    ax.legend(fontsize=10, facecolor=background_color, edgecolor=text_color)
    ax.grid(True, alpha=0.1, color=text_color, linestyle='--')

    plt.tight_layout()
    plt.show()
