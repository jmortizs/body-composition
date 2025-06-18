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
    x_values = []
    y_values = []
    async for doc in cursor:
        x_val = round(doc[f'avg{x_field}'], 2)
        y_val = round(doc[f'avg{y_field}'], 2)
        results.append(ScatterPoint(
            x=x_val,
            y=y_val,
            date=datetime.fromisoformat(doc['_id']),
            elapseDays=(datetime.fromisoformat(doc['_id']) - start).days
        ))
        x_values.append(x_val)
        y_values.append(y_val)

    # Calculate correlation coefficient (Pearson)
    correlation = None
    if len(x_values) > 1 and len(y_values) > 1:
        try:
            import numpy as np
            correlation = float(np.corrcoef(x_values, y_values)[0, 1])
        except Exception:
            correlation = None
    else:
        correlation = None

    answer = MetricsRelationshipChart(
        title=f"{display_units_map[x_field]['display_name']} vs {display_units_map[y_field]['display_name']} (total records: {len(results)})",
        xAxisTitle=f"{display_units_map[x_field]['display_name']} ({display_units_map[x_field]['units']})",
        yAxisTitle=f"{display_units_map[y_field]['display_name']} ({display_units_map[y_field]['units']})",
        correlation=correlation,
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

    # Convert to Polars DataFrame (ensure measureDate is datetime)
    df = pl.DataFrame(data)
    if df['measureDate'].dtype != pl.Datetime:
        df = df.with_columns([
            pl.col("measureDate").str.strptime(pl.Datetime, fmt=None, strict=False).alias("measureDate")
        ])

    # If max date is before the end date, set the end date to the max date
    max_date = df['measureDate'].max()
    if max_date < end:
        end = max_date.replace(hour=0, minute=0, second=0, microsecond=0)

    # Use Polars lazy API for efficient processing
    ldf = df.lazy()

    # Calculate days since start and group number
    ldf = ldf.with_columns([
        ((pl.col("measureDate") - pl.lit(start)).dt.total_days()).alias("days_since_start"),
        ( ( (pl.col("measureDate") - pl.lit(start)).dt.total_days() // group_time ).cast(pl.Int32) ).alias("time_group"),
    ])

    # Group by time_group and aggregate
    grouped_ldf = ldf.group_by("time_group").agg([
        pl.col(measure_field).mean().alias("mean_value"),
        pl.col(measure_field).std().alias("std_value"),
        pl.col("measureDate").min().alias("group_start_date"),
        pl.col("measureDate").max().alias("group_end_date"),
    ]).sort("time_group")

    grouped_df = grouped_ldf.with_columns([
        pl.col("std_value").fill_null(0)
    ]).collect()

    # Use the midpoint of each group as the representative date
    results = []
    for row in grouped_df.iter_rows(named=True):
        group_start_date = row["group_start_date"]
        group_end_date = row["group_end_date"]
        # Calculate midpoint between group_start_date and group_end_date
        if group_start_date and group_end_date:
            midpoint_timestamp = group_start_date.timestamp() + (group_end_date.timestamp() - group_start_date.timestamp()) / 2
            representative_date = datetime.fromtimestamp(midpoint_timestamp)
        else:
            # Fallback: use group_start_date or start
            representative_date = group_start_date or start
        # Cap the representative date at the actual end date if it exceeds it
        if representative_date > end:
            representative_date = end
        results.append(TimeProgressionPoint(
            value=round(row["mean_value"], 2) if row["mean_value"] is not None else None,
            std=round(row["std_value"], 2) if row["std_value"] is not None else 0,
            date=representative_date
        ))

    # Create the response
    answer = TimeProgressionChart(
        title=f"{display_units_map[measure_field]['display_name']} Progression\n({group_time} days intervals)",
        xAxisTitle="Date",
        yAxisTitle=f"{display_units_map[measure_field]['display_name']} ({display_units_map[measure_field]['units']})",
        dataPoints=results
    )

    return answer