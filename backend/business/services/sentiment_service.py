from typing import Optional
from backend.business.repository.sentiment_repository import SentimentRepository

class SentimentService:
    def __init__(self, repo: SentimentRepository):
        self._repo = repo

    def get_sentiment_analysis(self, major: str) -> Optional[dict]:
        row = self._repo.get_by_major(major)
        if row is None:
            return None

        pos = float(row["weighted_pos_total"])
        neg = float(row["weighted_neg_total"])
        likes = int(row["total_likes"])
        count = int(row["record_count"])

        pos_ratio = pos / (pos + neg) if (pos + neg) != 0 else 0.0
        avg_likes = likes / count if count != 0 else 0.0

        return {
            "major": major,
            "weighted_pos_total": pos,
            "weighted_neg_total": neg,
            "total_likes": likes,
            "record_count": count,
            "positive_ratio": round(pos_ratio, 4),
            "avg_likes": round(avg_likes, 2)
        }