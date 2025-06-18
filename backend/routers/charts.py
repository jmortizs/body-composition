from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import AsyncMongoClient
import polars as pl

from backend.db import MongoDBClient
from backend.models import MetricsRelationshipChart, ScatterPoint, TimeProgressionChart, TimeProgressionPoint

router = APIRouter()

display_units_map = {
    'muscleMass': {'units': 'kg', 'display_name': 'Muscle Mass'},
    'weight': {'units': 'kg', 'display_name': 'Weight'},
    'bodyFatMass': {'units': 'Kg', 'display_name': 'Body Fat Mass'},
    'totalBodyWater': {'units': 'Kg', 'display_name': 'Total Body Water'},
    'basalMetabolicRate': {'units': 'Kcal', 'display_name': 'Basal Metabolic Rate'},
}


@router.get("/measurements", response_model=MetricsRelationshipChart)
async def get_scatter(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)", example="2025-01-01"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)", example=datetime.now().strftime("%Y-%m-%d")),
    x_field: str = Query(..., description="Field for X axis", example="muscleMass"),
    y_field: str = Query(..., description="Field for Y axis", example="weight"),
    db: AsyncMongoClient = Depends(MongoDBClient.get_database)
):
    # Validate date format
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    # Validate fields
    allowed_fields = {"muscleMass", "weight", "bodyFatMass", "totalBodyWater", "basalMetabolicRate"}
    if x_field not in allowed_fields or y_field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid field selection")
    # Query MongoDB
    collection = db.get_collection("body_composition")

    pipeline = [
        {
            '$match': {
                'measureDate': {
                    '$gte': start,
                    '$lte': end
                }
            }
        }, {
            '$addFields': {
                'day': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$measureDate'
                    }
                }
            }
        }, {
            '$group': {
                '_id': '$day',
                f'avg{x_field}': {'$avg': f'${x_field}'},
                f'avg{y_field}': {'$avg': f'${y_field}'},
            }
        }, {
            '$sort': {
                '_id': 1
            }
        }
    ]

    cursor = await collection.aggregate(pipeline)
    results = []
    async for doc in cursor:
        results.append(ScatterPoint(
            x=round(doc[f'avg{x_field}'], 2),
            y=round(doc[f'avg{y_field}'], 2),
            date=datetime.fromisoformat(doc['_id']),
            elapseDays=(datetime.fromisoformat(doc['_id']) - start).days
        ))

    answer = MetricsRelationshipChart(
        title=f"{display_units_map[x_field]['display_name']} vs {display_units_map[y_field]['display_name']} (total records: {len(results)})",
        xAxisTitle=f"{display_units_map[x_field]['display_name']} ({display_units_map[x_field]['units']})",
        yAxisTitle=f"{display_units_map[y_field]['display_name']} ({display_units_map[y_field]['units']})",
        dataPoints=results
    )

    return answer


@router.get("/time-progression", response_model=TimeProgressionChart)
async def get_time_progression(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)", example="2025-01-01"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)", example=datetime.now().strftime("%Y-%m-%d")),
    measure_field: str = Query(..., description="Field for X axis", example="muscleMass"),
    group_time: int = Query(..., description="Group time in days", ge=7, example=28),
    db: AsyncMongoClient = Depends(MongoDBClient.get_database)
):
    # Validate date format
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    # Validate group_time
    if group_time <= 0:
        raise HTTPException(status_code=400, detail="Group time must be greater than 0")

    # Validate fields
    allowed_fields = {"muscleMass", "weight", "bodyFatMass", "totalBodyWater", "basalMetabolicRate"}
    if measure_field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid field selection")

    # Query MongoDB
    collection = db.get_collection("body_composition")

    match = {
        'measureDate': {
            '$gte': start,
            '$lte': end
        }
    }

    cursor = collection.find(match, projection={measure_field: 1, 'measureDate': 1, '_id': 0})
    data: list[dict] = []
    async for doc in cursor:
        data.append(doc)

    if not data:
        raise HTTPException(status_code=404, detail="No data found for the specified date range")

    # Convert to Polars DataFrame for efficient processing
    df = pl.DataFrame(data)

    # if max date is before the end date, set the end date to the max date
    if df['measureDate'].max() < end:
        end = df['measureDate'].max().replace(hour=0, minute=0, second=0, microsecond=0)

    # Add a column for the time group (period number)
    # Calculate days since start date and group by the specified interval
    df = df.with_columns([
        # Calculate days since start date
        ((pl.col("measureDate") - start).dt.total_days()).alias("days_since_start"),
    ])

    # Create time groups based on the group_time parameter
    df = df.with_columns([
        # Group number (0-indexed)
        (pl.col("days_since_start") // group_time).cast(pl.Int32).alias("time_group")
    ])

    # Group by time periods and calculate mean
    grouped_df = df.group_by("time_group").agg([
        pl.col(measure_field).mean().alias("mean_value"),
        pl.col(measure_field).std().alias("std_value"),
        pl.col("measureDate").min().alias("group_start_date"),  # Use the earliest date in the group as representative
    ]).sort("time_group")

            # Convert to TimeProgressionPoint objects
    results = []
    for row in grouped_df.iter_rows(named=True):
        # Calculate the representative date for this group (end of the period)
        group_start_days = row["time_group"] * group_time
        group_end_days = group_start_days + group_time
        representative_date = start + timedelta(days=group_end_days)

        # Cap the representative date at the actual end date if it exceeds it
        if representative_date > end:
            representative_date = end

        results.append(TimeProgressionPoint(
            value=round(row["mean_value"], 2),
            std=round(row["std_value"], 2),
            date=representative_date
        ))

    # Create the response
    answer = TimeProgressionChart(
        title=f"{display_units_map[measure_field]['display_name']} Progression (grouped by {group_time} days, {len(results)} periods)",
        xAxisTitle="Date",
        yAxisTitle=f"{display_units_map[measure_field]['display_name']} ({display_units_map[measure_field]['units']})",
        dataPoints=results
    )

    return answer