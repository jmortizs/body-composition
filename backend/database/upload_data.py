import os

import polars as pl
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

load_dotenv()

def read_from_csv(file_path: str) -> pl.DataFrame:

    df = pl.read_csv(
            file_path,
            skip_rows=1,
            has_header=True,
            truncate_ragged_lines=True,
            infer_schema_length=1000,  # Better type inference
            try_parse_dates=True,  # Try to parse dates automatically
        )

    return df

def upload_body_composition_data(data: pl.DataFrame):

    # Select and process columns in a single operation
    data = (
        data.select([
            "create_time",
            "time_offset",
            "weight",
            "skeletal_muscle_mass",
            "body_fat_mass",
            "basal_metabolic_rate",
            "total_body_water",
            "deviceuuid",
        ])
        .with_columns([
            # Convert create_time to datetime if not already
            pl.col("create_time").cast(pl.Datetime),
            pl.col("time_offset").cast(str),
            # Convert numeric columns and round
            pl.col("weight").cast(float).round(2),
            pl.col("skeletal_muscle_mass").cast(float).round(2),
            pl.col("body_fat_mass").cast(float).round(2),
            pl.col("basal_metabolic_rate").cast(int),
            pl.col("total_body_water").cast(float).round(2),
        ])
    )

    # rename columns
    data = data.rename(
        {
            "create_time": "measureDate",
            "time_offset": "timeOffset",
            "weight": "weight",
            "skeletal_muscle_mass": "muscleMass",
            "body_fat_mass": "bodyFatMass",
            "basal_metabolic_rate": "basalMetabolicRate",
            "deviceuuid": "deviceId",
            "total_body_water": "totalBodyWater"
        }
    )

    # drop rows with null values
    data = data.drop_nulls()

    # connet to mongo db
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("DATABASE_NAME")]
    collection = db['body_composition']

    # Prepare bulk upsert operations
    operations = [
        UpdateOne(
            {"measureDate": record["measureDate"], "deviceId": record["deviceId"]},
            {"$set": record},
            upsert=True
        )
        for record in data.to_dicts()
    ]

    if operations:
        result = collection.bulk_write(operations, ordered=False)
        inserted = result.upserted_count
        updated = result.modified_count
        print(f"Inserted: {inserted}, Updated: {updated}")


if __name__ == "__main__":
    df = read_from_csv("data.csv")
    upload_body_composition_data(df)
