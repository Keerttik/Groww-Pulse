from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Optional, List, Tuple

@dataclass
class Review:
    rating: int
    text: str
    thumbs_up: int
    app_version: Optional[str]

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(
            rating=data['rating'],
            text=data['text'],
            thumbs_up=data['thumbs_up'],
            app_version=data.get('app_version')
        )

@dataclass
class ReviewEmbedding:
    review: Review
    vector: List[float]

    def to_dict(self):
        return {
            "review": self.review.to_dict(),
            "vector": self.vector
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            review=Review.from_dict(data['review']),
            vector=data['vector']
        )

@dataclass
class Cluster:
    cluster_id: int
    reviews: List[Review]
    centroid: List[float]
    size: int

    def to_dict(self):
        return {
            "cluster_id": self.cluster_id,
            "reviews": [r.to_dict() for r in self.reviews],
            "centroid": self.centroid,
            "size": self.size
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            cluster_id=data['cluster_id'],
            reviews=[Review.from_dict(r) for r in data['reviews']],
            centroid=data['centroid'],
            size=data['size']
        )

@dataclass
class Theme:
    name: str
    description: str
    review_count: int
    sentiment: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Quote:
    text: str
    rating: int
    validated: bool

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class ActionIdea:
    title: str
    description: str
    related_theme: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class PulseReport:
    product: str
    iso_week: str
    generated_at: datetime
    review_window: Tuple[date, date]
    total_reviews_analyzed: int
    themes: List[Theme]
    quotes: List[Quote]
    action_ideas: List[ActionIdea]
    app_info: dict

    def to_dict(self):
        return {
            "product": self.product,
            "iso_week": self.iso_week,
            "generated_at": self.generated_at.isoformat(),
            "review_window": [d.isoformat() for d in self.review_window],
            "total_reviews_analyzed": self.total_reviews_analyzed,
            "themes": [t.to_dict() for t in self.themes],
            "quotes": [q.to_dict() for q in self.quotes],
            "action_ideas": [a.to_dict() for a in self.action_ideas],
            "app_info": self.app_info
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            product=data['product'],
            iso_week=data['iso_week'],
            generated_at=datetime.fromisoformat(data['generated_at']),
            review_window=(date.fromisoformat(data['review_window'][0]), date.fromisoformat(data['review_window'][1])),
            total_reviews_analyzed=data['total_reviews_analyzed'],
            themes=[Theme.from_dict(t) for t in data['themes']],
            quotes=[Quote.from_dict(q) for q in data['quotes']],
            action_ideas=[ActionIdea.from_dict(a) for a in data['action_ideas']],
            app_info=data['app_info']
        )

@dataclass
class RunRecord:
    run_id: str
    product: str
    iso_week: str
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    reviews_fetched: int
    clusters_found: int
    themes_generated: int
    doc_heading_anchor: Optional[str]
    doc_id: Optional[str]
    email_message_id: Optional[str]
    email_mode: str
    llm_tokens_used: int
    error_message: Optional[str]

    def to_dict(self):
        d = asdict(self)
        d['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            d['completed_at'] = self.completed_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data):
        completed_at = data.get('completed_at')
        if completed_at:
            completed_at = datetime.fromisoformat(completed_at)
        return cls(
            run_id=data['run_id'],
            product=data['product'],
            iso_week=data['iso_week'],
            started_at=datetime.fromisoformat(data['started_at']),
            completed_at=completed_at,
            status=data['status'],
            reviews_fetched=data['reviews_fetched'],
            clusters_found=data['clusters_found'],
            themes_generated=data['themes_generated'],
            doc_heading_anchor=data.get('doc_heading_anchor'),
            doc_id=data.get('doc_id'),
            email_message_id=data.get('email_message_id'),
            email_mode=data['email_mode'],
            llm_tokens_used=data['llm_tokens_used'],
            error_message=data.get('error_message')
        )
