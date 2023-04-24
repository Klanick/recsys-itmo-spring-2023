from .toppop import TopPop
from .recommender import Recommender
import random


class Solution(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    sum_recs = dict()

    def __init__(self, tracks_redis, catalog):
        self.tracks_redis = tracks_redis
        self.fallback = TopPop(tracks_redis.connection, catalog.top_tracks[:100])
        self.catalog = catalog

    def update_recs(self, user: int, track: int, metric_value: float, rec_size: int = 1):
        cross_cofficient = 1.25
        metric_degree = 2

        if track not in self.sum_recs[user]:
            self.sum_recs[user][track] = 0
        self.sum_recs[user][track] *= metric_value * cross_cofficient
        self.sum_recs[user][track] += metric_value ** metric_degree / rec_size

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        if user not in self.sum_recs:
            self.sum_recs[user] = dict()

        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        previous_track = self.catalog.from_bytes(previous_track)
        recommendations = previous_track.recommendations
        if not recommendations:
            if len(self.sum_recs[user]) == 0:
                return self.fallback.recommend_next(user, prev_track, prev_track_time)
        else:
            for rec_track in recommendations:
                self.update_recs(user=user, track=rec_track, metric_value=prev_track_time,
                                 rec_size=len(recommendations))

        return random.choices(list(self.sum_recs[user].keys()), weights=list(self.sum_recs[user].values()))[0]
