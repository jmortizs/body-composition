from typing import Literal, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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


def plot_daily_progress(
    df: pl.DataFrame,
    metric: Literal["weight", "muscle_mass", "body_fat_mass", "basal_metabolic_rate", "body_fat_mass_percentage", "muscle_mass_percentage"],
    figsize: tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    use_elapsed_days: bool = True,
) -> None:
    """
    Create a scatter plot showing daily progress of a given metric over time with a linear regression trend line.

    Args:
        df: Polars DataFrame containing body composition data with columns including the specified metric
            and either 'elapse_days' or 'create_time'
        metric: The metric to plot progress for
        figsize: Figure size as (width, height) in inches
        title: Optional title for the plot. If None, a default title will be generated
        x_label: Optional label for the x-axis. If None, will use "Days Elapsed" or "Date"
        y_label: Optional label for the y-axis. If None, the metric name will be used
        use_elapsed_days: If True, use elapse_days for x-axis. If False, use create_time

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

    # Validate required columns
    if metric not in df.columns:
        raise ValueError(f"DataFrame must contain '{metric}' column.")

    x_column = "elapse_days" if use_elapsed_days else "create_time"
    if x_column not in df.columns:
        raise ValueError(f"DataFrame must contain '{x_column}' column.")

    # Handle edge cases
    if df.is_empty():
        raise ValueError("DataFrame is empty.")

    # Prepare data for plotting
    plot_data = df.select([x_column, metric]).drop_nulls()

    if plot_data.is_empty():
        raise ValueError(f"No valid data points found for {metric} and {x_column}.")

    # Convert to pandas for seaborn compatibility if using create_time
    if use_elapsed_days:
        x_data = plot_data.get_column(x_column).to_numpy()
        y_data = plot_data.get_column(metric).to_numpy()
        plot_df = plot_data.to_pandas()
    else:
        # For datetime plotting, convert to pandas
        plot_df = plot_data.to_pandas()
        x_data = np.arange(len(plot_df))  # Use numeric index for regression
        y_data = plot_df[metric].to_numpy()

    # ----- Main Plot -----
    main_color = '#2293f5'

    if use_elapsed_days:
        # Scatter plot with elapse_days
        ax.scatter(
            x_data,
            y_data,
            color=main_color,
            alpha=0.6,
            s=25,
            edgecolors='white',
            linewidth=0.5
        )
        x_for_regression = x_data
    else:
        # Scatter plot with dates
        ax.scatter(
            plot_df[x_column],
            y_data,
            color=main_color,
            alpha=0.6,
            s=25,
            edgecolors='white',
            linewidth=0.5
        )
        x_for_regression = x_data  # Use numeric index for regression calculation

    # Calculate linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_for_regression, y_data)

    # Create regression line
    if use_elapsed_days:
        x_line = np.linspace(x_data.min(), x_data.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color='#f52245', linestyle='--', linewidth=2, alpha=0.95,
                label=f'Trend: {slope:.3f}/day (R² = {r_value**2:.3f})')
    else:
        x_line_numeric = np.linspace(0, len(plot_df) - 1, 100)
        y_line = slope * x_line_numeric + intercept
        # Convert numeric line back to datetime for plotting
        x_line_dates = pd.date_range(start=plot_df[x_column].min(),
                                   end=plot_df[x_column].max(),
                                   periods=100)
        ax.plot(x_line_dates, y_line, color='#f52245', linestyle='--', linewidth=2, alpha=0.95,
                label=f'Trend: {slope:.3f}/day (R² = {r_value**2:.3f})')

    # Calculate overall progress
    first_value, last_value = y_data[0], y_data[-1]
    total_change = last_value - first_value
    total_change_percent = (total_change / first_value) * 100 if first_value != 0 else 0

    # ----- Labels and Aesthetics -----
    # Set title if provided, otherwise generate one
    if title is None:
        period_text = f"{len(y_data)} days" if use_elapsed_days else f"{len(y_data)} records"
        title = (f"{metric.replace('_', ' ').title()} Daily Progress\n"
                f"Total Change: {total_change:+.2f} ({total_change_percent:+.1f}%) over {period_text}")

    ax.set_title(title, fontsize=14, pad=20, color=text_color)

    # Set axis labels
    if x_label is None:
        x_label = "Days Elapsed" if use_elapsed_days else "Date"
    if y_label is None:
        y_label = metric.replace("_", " ").title()

    ax.set_xlabel(x_label, fontsize=12, color=text_color)
    ax.set_ylabel(y_label, fontsize=12, color=text_color)

    # Format x-axis for dates
    if not use_elapsed_days:
        ax.tick_params(axis='x', rotation=45)

    ax.tick_params(axis='both', labelsize=10)

    # Style the spines
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(text_color)

    # Add legend
    ax.legend(fontsize=10, facecolor=background_color, edgecolor=text_color)

    # Add grid
    ax.grid(True, alpha=0.1, color=text_color, linestyle='--')

    plt.tight_layout()
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


def plot_monthly_progress_boxplot(
    df: pl.DataFrame,
    metric: Literal["weight", "muscle_mass", "body_fat_mass"],
    figsize: tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    y_label: Optional[str] = None,
    positive_change: bool = True,
) -> None:
    """
    Create a box plot showing monthly progress for a given metric, displaying the distribution
    of values for each month. Processes daily records by extracting month from create_time.

    Args:
        df: Polars DataFrame containing daily body composition data with columns:
            create_time, weight, muscle_mass, body_fat_mass, basal_metabolic_rate, elapse_days
        metric: The metric to plot (weight, muscle_mass, or body_fat_mass).
        figsize: Size of the plot as (width, height) in inches.
        title: Optional custom title for the plot.
        y_label: Optional label for the y-axis.
        positive_change: Whether positive changes are considered good (affects color coding).

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

    # Prepare data for box plot
    if "create_time" not in df.columns or metric not in df.columns:
        raise ValueError(f"DataFrame must contain 'create_time' and '{metric}' columns.")

    # Extract month-year from create_time and add as a new column
    df_with_month = df.with_columns([
        pl.col("create_time").dt.strftime("%Y-%m").alias("month")
    ]).select(["month", metric])

    # Convert to pandas for seaborn compatibility
    df_pandas = df_with_month.to_pandas()

    # Handle edge cases
    if df_pandas.empty:
        raise ValueError("DataFrame is empty.")

    # Calculate monthly statistics for annotations
    monthly_stats = (
        df_with_month.group_by("month")
        .agg([
            pl.col(metric).mean().alias("mean"),
            pl.col(metric).median().alias("median"),
            pl.col(metric).count().alias("count")
        ])
        .sort("month")
    )

    # Calculate overall progress
    first_month_data = df_with_month.filter(pl.col("month") == monthly_stats["month"][0])[metric]
    last_month_data = df_with_month.filter(pl.col("month") == monthly_stats["month"][-1])[metric]

    if len(first_month_data) > 0 and len(last_month_data) > 0:
        first_median = first_month_data.median()
        last_median = last_month_data.median()
        total_variation = last_median - first_median
        total_variation_percent = (total_variation / first_median) * 100 if first_median else 0
    else:
        total_variation = 0
        total_variation_percent = 0

    # ----- Main Plot -----
    main_color = '#00bfff'

    # Create box plot
    box_plot = sns.boxplot(
        data=df_pandas,
        x="month",
        y=metric,
        ax=ax,
        color=main_color,
        boxprops=dict(facecolor=main_color, alpha=0.3, edgecolor=main_color),
        whiskerprops=dict(color=main_color),
        capprops=dict(color=main_color),
        medianprops=dict(color='#eb3f7b', linewidth=2),
        showfliers=False  # Hide outliers
    )

    # ----- Annotations -----
    # Add only median values (remove month-to-month change annotations)
    medians = monthly_stats["median"].to_list()
    months = monthly_stats["month"].to_list()

    for i, (month, median) in enumerate(zip(months, medians)):
        # Show only median value
        ax.annotate(
            f"{median:.1f}",
            (i, median),
            xytext=(0, 5),
            textcoords='offset points',
            ha='center',
            fontsize=9,
            color=text_color,
            alpha=0.95
        )

    # ----- Labels and Aesthetics -----
    auto_title = (
        f"{metric.replace('_', ' ').title()} Distribution by Month\n"
        f"Total Change: {total_variation:+.2f} ({total_variation_percent:+.1f}%)"
    )
    ax.set_title(title or auto_title, fontsize=14, pad=20)

    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel(y_label or metric.replace("_", " ").title(), fontsize=12)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    # Style the spines
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(text_color)

    # Add grid
    ax.grid(True, alpha=0.1, color=text_color, linestyle='--')

    plt.tight_layout()
    plt.show()


def plot_monthly_body_composition_stacked(
    df: pl.DataFrame,
    figsize: tuple[int, int] = (12, 6),
    title: Optional[str] = None,
    y_label: Optional[str] = None,
) -> None:
    """
    Create a stacked horizontal bar plot showing monthly averages of body fat and muscle mass percentages.

    Args:
        df: Polars DataFrame containing daily body composition data with columns:
            create_time, body_fat_mass_percentage, muscle_mass_percentage
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

    # Validate required columns
    required_columns = ["create_time", "body_fat_mass_percentage", "muscle_mass_percentage"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"DataFrame must contain columns: {missing_columns}")

    # Handle edge cases
    if df.is_empty():
        raise ValueError("DataFrame is empty.")

    # Extract month-year from create_time and calculate monthly averages
    monthly_data = (
        df.with_columns([
            pl.col("create_time").dt.strftime("%Y-%m").alias("month")
        ])
        .group_by("month")
        .agg([
            pl.col("body_fat_mass_percentage").mean().alias("body_fat_avg"),
            pl.col("muscle_mass_percentage").mean().alias("muscle_mass_avg"),
            pl.col("body_fat_mass_percentage").count().alias("count")
        ])
        .sort("month")
    )

    # Extract data for plotting
    months = monthly_data.get_column("month").to_list()
    body_fat_avg = monthly_data.get_column("body_fat_avg").to_numpy()
    muscle_mass_avg = monthly_data.get_column("muscle_mass_avg").to_numpy()

    # ----- Main Plot -----
    y_pos = np.arange(len(months))
    height = 0.6
    bar_alpha = 0.90

    # Define colors consistent with the theme
    body_fat_color = '#ff6b6b'  # Red for body fat
    muscle_mass_color = '#00bfff'  # Blue for muscle mass

    # Create stacked horizontal bars
    bars1 = ax.barh(y_pos, body_fat_avg, height,
                    label='Body Fat %', color=body_fat_color, alpha=bar_alpha)
    bars2 = ax.barh(y_pos, muscle_mass_avg, height, left=body_fat_avg,
                    label='Muscle Mass %', color=muscle_mass_color, alpha=bar_alpha)

    # ----- Annotations -----
    # Add value annotations on each segment
    for i, (bf, mm) in enumerate(zip(body_fat_avg, muscle_mass_avg)):
        # Body fat percentage annotation
        ax.annotate(
            f"{bf:.1f}%",
            (bf/2, i),
            ha='center',
            va='center',
            fontsize=10,
            color='white',
            weight='bold'
        )

        # Muscle mass percentage annotation
        ax.annotate(
            f"{mm:.1f}%",
            (bf + mm/2, i),
            ha='center',
            va='center',
            fontsize=10,
            color='white',
            weight='bold'
        )

    # ----- Labels and Aesthetics -----
    auto_title = "Monthly Body Composition Averages\nBody Fat % and Muscle Mass %"
    ax.set_title(title or auto_title, fontsize=14, pad=20)

    ax.set_xlabel(y_label or "Percentage (%)", fontsize=12)
    ax.set_ylabel("Month", fontsize=12)

    # Set y-axis labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(months)

    ax.tick_params(axis='x', labelsize=10)
    ax.tick_params(axis='y', labelsize=10)

    # Style the spines
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(text_color)

    # Add legend
    ax.legend(fontsize=10, facecolor=background_color, edgecolor=text_color, loc='upper right')

    # Add grid
    ax.grid(True, alpha=0.1, color=text_color, linestyle='--', axis='x')

    # Set x-axis to start from 0 for better visualization
    ax.set_xlim(left=0)

    plt.tight_layout()
    plt.show()
