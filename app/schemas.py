from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str


class SigninInput(BaseModel):
    email: str
    password: str
    device_id: str = "portfolio-device"


class RefreshInput(BaseModel):
    user_id: str
    device_id: str = "portfolio-device"
    refresh_token: str


class LotOut(BaseModel):
    id: str
    lotNo: str
    productSku: str
    productName: str
    machine: str
    startedAt: datetime
    defectRate: float
    sampleCount: int
    status: Literal["shipping_hold", "review", "released"]


class DashboardOut(BaseModel):
    lots: list[LotOut]
    machineScores: list[dict[str, str | float]]
    topDefects: list[dict[str, str | int | float]]


class InspectionResultIn(BaseModel):
    time: datetime
    lot_id: str
    machine_id: str
    image_id: str
    defect_type: str
    score: float
    ai_label: str


class BulkInspectionIn(BaseModel):
    results: list[InspectionResultIn]


class ReviewQueueOut(BaseModel):
    id: str
    lotId: str
    lotNo: str
    reason: str
    status: str
    assignedTo: str
    createdAt: datetime


class ReviewPatch(BaseModel):
    status: Literal["open", "approved", "rejected"]
    memo: str = ""
