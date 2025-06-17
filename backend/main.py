from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from backend.db import MongoDBClient
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.models import MetricsRelationshipChart, ScatterPoint
from pymongo import AsyncMongoClient

display_units_map = {
    'muscleMass': {'units': 'kg', 'display_name': 'Muscle Mass'},
    'weight': {'units': 'kg', 'display_name': 'Weight'},
    'bodyFatMass': {'units': 'Kg', 'display_name': 'Body Fat Mass'},
    'totalBodyWater': {'units': 'Kg', 'display_name': 'Total Body Water'},
    'basalMetabolicRate': {'units': 'Kcal', 'display_name': 'Basal Metabolic Rate'},
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await MongoDBClient.get_client()
    yield
    await MongoDBClient.close_client()

app = FastAPI(lifespan=lifespan)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/measurements/scatter", response_model=MetricsRelationshipChart)
async def get_scatter(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    x_field: str = Query(..., description="Field for X axis"),
    y_field: str = Query(..., description="Field for Y axis"),
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
