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
            - skeletal_muscle_mass: in kg (rounded to 2 decimal places)
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

        # Apply date range filters
        if date_from:
            df = df.filter(pl.col("create_time") >= date_from)
        if date_to:
            df = df.filter(pl.col("create_time") <= date_to)

        # Sort by create_time
        df = df.sort("create_time", descending=False)

        # Remove duplicates by keeping first record per day
        df = (
            df.with_columns(pl.col("create_time").dt.date().alias("date"))
            .unique(subset=["date"], keep="first")
            .drop("date")
        )

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