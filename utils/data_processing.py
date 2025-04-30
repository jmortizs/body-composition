import polars as pl
from datetime import datetime
from typing import Optional

def load_data(
    file_path: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    device_id: Optional[str] = None,
) -> pl.DataFrame:
    """
    Load and process body composition data from a CSV file.

    The function performs the following operations:
    1. Loads data from CSV, skipping the first row and using the second as header
    2. Filters by device ID if specified
    3. Selects and processes relevant columns
    4. Converts data types and rounds numeric values
    5. Removes duplicate records per day, keeping the first measurement
    6. Calculates days elapsed since first measurement

    Args:
        file_path (str): Path to the CSV file containing body composition data
        date_from (str, optional): Start date in YYYY-MM-DD format. Defaults to None.
        date_to (str, optional): End date in YYYY-MM-DD format. Defaults to None.
        device_id (str, optional): Device UUID to filter data. Defaults to None.

    Returns:
        pl.DataFrame: Processed data with columns:
            - create_time: datetime of measurement
            - weight: body weight in kg (rounded to 2 decimal places)
            - muscle_mass: in kg (rounded to 2 decimal places)
            - body_fat_mass: in kg (rounded to 2 decimal places)
            - basal_metabolic_rate: in kcal (integer)
            - elapse_days: days since first measurement

    Raises:
        FileNotFoundError: If the specified file_path does not exist
        ValueError: If date_from or date_to are not in YYYY-MM-DD format
    """
    try:
        # Read CSV file with optimized settings
        df = pl.read_csv(
            file_path,
            skip_rows=1,
            has_header=True,
            truncate_ragged_lines=True,
            infer_schema_length=1000,  # Better type inference
            try_parse_dates=True,  # Try to parse dates automatically
        )

        # Validate and parse date filters
        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_from must be in YYYY-MM-DD format")

        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_to must be in YYYY-MM-DD format")

        # Filter by device ID if specified
        if device_id:
            df = df.filter(pl.col("deviceuuid") == device_id)

        # Select and process columns in a single operation
        df = (
            df.select([
                "create_time",
                "weight",
                "skeletal_muscle_mass",
                "body_fat_mass",
                "basal_metabolic_rate"
            ])
            .with_columns([
                # Convert create_time to datetime if not already
                pl.col("create_time").cast(pl.Datetime),
                # Convert numeric columns and round
                pl.col("weight").cast(float).round(2),
                pl.col("skeletal_muscle_mass").cast(float).round(2),
                pl.col("body_fat_mass").cast(float).round(2),
                pl.col("basal_metabolic_rate").cast(int)
            ])
        )

        # rename skeletal_muscle_mass to muscle_mass
        df = df.rename({"skeletal_muscle_mass": "muscle_mass"})

        # Apply date range filters
        if date_from:
            df = df.filter(pl.col("create_time") >= date_from)
        if date_to:
            df = df.filter(pl.col("create_time") <= date_to)

        # Sort by create_time
        df = df.sort("create_time", descending=False)

        # Calculate mean values for each day
        df = (
            df.with_columns(pl.col("create_time").dt.date().alias("date"))
            .group_by("date")
            .agg([
                pl.col("create_time").first(),  # Keep first timestamp of the day
                pl.col("weight").mean().round(2),
                pl.col("muscle_mass").mean().round(2),
                pl.col("body_fat_mass").mean().round(2),
                pl.col("basal_metabolic_rate").mean().round(0).cast(int)
            ])
            .drop("date")
        )

        # drop rows with null values
        df = df.drop_nulls()

        # Calculate days elapsed since first record
        first_date = df.select("create_time").min()
        df = df.with_columns(
            (pl.col("create_time") - first_date).dt.total_days().alias("elapse_days")
        )

        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error processing data: {str(e)}")


def calculate_monthly_stats(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate monthly statistics for body composition metrics.

    For each metric (weight, muscle_mass, body_fat_mass, basal_metabolic_rate),
    this function calculates:
    - Mean value
    - Standard deviation
    - IQR (Interquartile Range)
    - Month-to-month variation (difference from previous month)

    Args:
        df (pl.DataFrame): DataFrame with body composition data, must contain:
            - create_time: datetime column
            - weight: float column
            - muscle_mass: float column
            - body_fat_mass: float column
            - basal_metabolic_rate: int column

    Returns:
        pl.DataFrame: Monthly statistics with columns:
            - month: YYYY-MM format
            - weight_mean, weight_std_dev, weight_iqr, weight_variation
            - muscle_mass_mean, muscle_mass_std_dev, muscle_mass_iqr, muscle_mass_variation
            - body_fat_mass_mean, body_fat_mass_std_dev, body_fat_mass_iqr, body_fat_mass_variation
            - basal_metabolic_rate_mean, basal_metabolic_rate_std_dev, basal_metabolic_rate_iqr, basal_metabolic_rate_month_to_month_change
    """
    # Extract month from create_time
    df = df.with_columns(
        pl.col("create_time").dt.strftime("%Y-%m").alias("month")
    )

    # Define metrics to analyze
    metrics = ["weight", "muscle_mass", "body_fat_mass", "basal_metabolic_rate"]

    # Calculate all statistics in one go
    monthly_stats = (
        df.group_by("month")
        .agg([
            # Record count
            pl.count().alias("record_count"),

            # Weight statistics
            pl.col("weight").mean().round(2).alias("weight_mean"),
            pl.col("weight").std().round(2).alias("weight_std_dev"),

            # Muscle mass statistics
            pl.col("muscle_mass").mean().round(2).alias("muscle_mass_mean"),
            pl.col("muscle_mass").std().round(2).alias("muscle_mass_std_dev"),

            # Body fat mass statistics
            pl.col("body_fat_mass").mean().round(2).alias("body_fat_mass_mean"),
            pl.col("body_fat_mass").std().round(2).alias("body_fat_mass_std_dev"),

            # Basal metabolic rate statistics
            pl.col("basal_metabolic_rate").mean().round(0).cast(int).alias("basal_metabolic_rate_mean"),
            pl.col("basal_metabolic_rate").std().round(0).cast(int).alias("basal_metabolic_rate_std_dev"),
        ])
        .sort("month")
    )

    # Calculate month-to-month changes for each metric
    for metric in metrics:
        mean_col = f"{metric}_mean"
        change_col = f"{metric}_variation"
        monthly_stats = monthly_stats.with_columns(
            (pl.col(mean_col) - pl.col(mean_col).shift(1)).round(2).alias(change_col)
        )

    return monthly_stats