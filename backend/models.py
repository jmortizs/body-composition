from pydantic import BaseModel, Field
from datetime import datetime

class ScatterPoint(BaseModel):
    x: float = Field(..., description="X-axis value", ge=0)
    y: float = Field(..., description="Y-axis value", ge=0)
    date: datetime = Field(..., description="Measurement date")
    elapseDays: int = Field(..., description="Elapse days since first measurement")

class MetricsRelationshipChart(BaseModel):
    title: str = Field(..., description="Chart title")
    xAxisTitle: str = Field(..., alias="xAxisTitle", description="X-axis title")
    yAxisTitle: str = Field(..., alias="yAxisTitle", description="Y-axis title")
    dataPoints: list[ScatterPoint] = Field(..., alias="dataPoints", description="Data points")



