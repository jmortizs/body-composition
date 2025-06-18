from pydantic import BaseModel, Field
from datetime import datetime


class BaseChart(BaseModel):
    title: str = Field(..., description="Chart title")
    xAxisTitle: str = Field(..., alias="xAxisTitle", description="X-axis title")
    yAxisTitle: str = Field(..., alias="yAxisTitle", description="Y-axis title")

class ScatterPoint(BaseModel):
    x: float = Field(..., description="X-axis value", ge=0)
    y: float = Field(..., description="Y-axis value", ge=0)
    date: datetime = Field(..., description="Measurement date")
    elapseDays: int = Field(..., description="Elapse days since first measurement")

class MetricsRelationshipChart(BaseChart):
    correlation: float = Field(..., description="Correlation coefficient")
    dataPoints: list[ScatterPoint] = Field(..., alias="dataPoints", description="Data points")

class TimeProgressionPoint(BaseModel):
    value: float = Field(..., description="Value")
    std: float = Field(..., description="Standard deviation")
    date: datetime = Field(..., description="Measurement date")


class TimeProgressionChart(BaseChart):
    dataPoints: list[TimeProgressionPoint] = Field(..., alias="dataPoints", description="Data points")



