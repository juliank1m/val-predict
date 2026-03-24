"""Elo rating engine with margin-of-victory adjustment and inactivity decay."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EloUpdate:
    """Result of a single Elo update."""

    team_id: int
    old_elo: float
    new_elo: float
    delta: float


@dataclass
class EloEngine:
    """Compute and track Elo ratings for teams.

    Parameters:
        k_factor: Base K-factor controlling rating volatility.
        start_elo: Default starting Elo for new teams.
        decay_days: Days of inactivity before decay kicks in.
        decay_rate: Fraction to decay toward start_elo per week past decay_days.
    """

    k_factor: float = 32.0
    start_elo: float = 1500.0
    decay_days: int = 60
    decay_rate: float = 0.02

    # Internal state: team_id -> current elo
    ratings: dict[int, float] = field(default_factory=dict)
    # team_id -> datetime of last map played
    last_played: dict[int, datetime] = field(default_factory=dict)

    def get_elo(self, team_id: int) -> float:
        """Get a team's current Elo, defaulting to start_elo."""
        return self.ratings.get(team_id, self.start_elo)

    def expected_score(self, elo_a: float, elo_b: float) -> float:
        """Probability that team A wins given both Elo ratings."""
        return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))

    def margin_of_victory_multiplier(self, round_diff: int) -> float:
        """Scale the K-factor by how dominant the win was.

        A 13-5 stomp (diff=8) gives ~2.2x multiplier.
        A 13-11 nailbiter (diff=2) gives ~1.1x multiplier.
        """
        return math.log(abs(round_diff) + 1)

    def apply_decay(self, team_id: int, current_date: datetime) -> float:
        """Decay a team's Elo toward start_elo if they've been inactive.

        Returns the decayed Elo (also updates internal state).
        """
        if team_id not in self.last_played:
            return self.get_elo(team_id)

        days_inactive = (current_date - self.last_played[team_id]).days
        if days_inactive <= self.decay_days:
            return self.get_elo(team_id)

        extra_weeks = (days_inactive - self.decay_days) / 7.0
        decay_factor = (1.0 - self.decay_rate) ** extra_weeks
        current_elo = self.get_elo(team_id)
        decayed_elo = self.start_elo + (current_elo - self.start_elo) * decay_factor
        self.ratings[team_id] = decayed_elo
        return decayed_elo

    def update(
        self,
        team1_id: int,
        team2_id: int,
        team1_rounds: int,
        team2_rounds: int,
        match_date: datetime,
    ) -> tuple[EloUpdate, EloUpdate]:
        """Process a single map result and return Elo updates for both teams.

        Args:
            team1_id: ID of team 1.
            team2_id: ID of team 2.
            team1_rounds: Rounds won by team 1.
            team2_rounds: Rounds won by team 2.
            match_date: When the map was played (for decay calculation).

        Returns:
            Tuple of (team1_update, team2_update).
        """
        # Apply inactivity decay before computing
        elo1 = self.apply_decay(team1_id, match_date)
        elo2 = self.apply_decay(team2_id, match_date)

        # Determine actual outcome (1.0 = team1 win, 0.0 = team2 win)
        if team1_rounds > team2_rounds:
            actual1 = 1.0
        elif team2_rounds > team1_rounds:
            actual1 = 0.0
        else:
            actual1 = 0.5  # Draw (shouldn't happen in Valorant, but handle it)

        expected1 = self.expected_score(elo1, elo2)

        round_diff = abs(team1_rounds - team2_rounds)
        mov = self.margin_of_victory_multiplier(round_diff)
        k = self.k_factor * mov

        delta1 = k * (actual1 - expected1)
        delta2 = -delta1

        new_elo1 = elo1 + delta1
        new_elo2 = elo2 + delta2

        # Update internal state
        self.ratings[team1_id] = new_elo1
        self.ratings[team2_id] = new_elo2
        self.last_played[team1_id] = match_date
        self.last_played[team2_id] = match_date

        return (
            EloUpdate(team_id=team1_id, old_elo=elo1, new_elo=new_elo1, delta=delta1),
            EloUpdate(team_id=team2_id, old_elo=elo2, new_elo=new_elo2, delta=delta2),
        )
