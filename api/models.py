from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class TransactionRequest(BaseModel):
    customer_id: str
    from_account_no: str
    from_account_currency: str
    to_account_no: str
    transaction_amount: float = Field(gt=0)
    transfer_currency: str
    transfer_type: str = Field(pattern="^[SILQO]$")
    charges_type: Optional[str] = ""
    swift: Optional[str] = ""
    check_constraint: bool = True
    datetime: Optional[datetime] = None
    bank_country: Optional[str] = "UAE"


class TransactionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    decision: str
    risk_score: float
    risk_level: str
    confidence_level: float
    model_agreement: float
    reasons: List[str]
    individual_scores: dict
    transaction_id: str
    processing_time_ms: int


class ApprovalRequest(BaseModel):
    transaction_id: str
    customer_id: str
    comments: Optional[str] = ""


class RejectionRequest(BaseModel):
    transaction_id: str
    customer_id: str
    reason: str


class ActionResponse(BaseModel):
    status: str
    transaction_id: str
    timestamp: str
    message: str
