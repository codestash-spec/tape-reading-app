from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    ACK = "ack"
    PARTIAL = "partial_fill"
    FILL = "fill"
    REJECT = "reject"
    CANCEL = "cancel"
    ERROR = "error"


class OrderRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    tif: str = "DAY"
    slippage_bps: Optional[float] = None
    max_show_size: Optional[float] = None
    post_only: bool = False
    reduce_only: bool = False
    dry_run: bool = False
    routing_hints: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, str] = Field(default_factory=dict)


class OrderEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    order_id: str
    symbol: str
    status: OrderStatus
    timestamp: datetime
    filled_qty: float = 0.0
    avg_price: Optional[float] = None
    reason: Optional[str] = None
    raw: Dict[str, str] = Field(default_factory=dict)
