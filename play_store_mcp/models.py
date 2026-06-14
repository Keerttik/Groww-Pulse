from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FormattedReview(BaseModel):
    rating: int
    text: str
    thumbs_up: int
    app_version: Optional[str] = None

class ReviewResponse(BaseModel):
    app_id: str
    fetched_at: str
    review_count: int
    reviews: List[FormattedReview]

class AppInfoResponse(BaseModel):
    app_id: str
    title: str
    rating: float
    ratings_count: int
    current_version: Optional[str] = None
    installs: str
    updated: Optional[int] = None
