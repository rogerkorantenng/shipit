"""Adaptive persona system for the StudyDrip tutor agent.

Manages the 3-axis persona state and transitions based on student performance.
"""

from dataclasses import dataclass, field


@dataclass
class PersonaState:
    """Tracks the current state of the tutor persona across 3 axes."""

    level: str = "beginner"  # beginner, intermediate, advanced
    momentum: str = "steady"  # struggling, steady, thriving
    mode: str = "explain"  # explain, quiz, socratic, review

    # Internal tracking
    recent_scores: list[float] = field(default_factory=list)
    interaction_count: int = 0
    quiz_count: int = 0

    def update_from_progress(self, progress: dict) -> None:
        """Update persona state from backend progress data."""
        if progress.get("level"):
            self.level = progress["level"]
        if progress.get("momentum"):
            self.momentum = progress["momentum"]
        self.recent_scores = progress.get("recent_scores", self.recent_scores)

    def record_quiz_score(self, score: float) -> None:
        """Record a quiz score and recalculate momentum."""
        self.recent_scores.append(score)
        # Keep last 5 scores for rolling average
        if len(self.recent_scores) > 5:
            self.recent_scores = self.recent_scores[-5:]
        self.quiz_count += 1
        self._recalculate_momentum()

    def _recalculate_momentum(self) -> None:
        """Recalculate momentum tier from recent scores."""
        if not self.recent_scores:
            return
        avg = sum(self.recent_scores) / len(self.recent_scores)
        if avg < 0.5:
            self.momentum = "struggling"
        elif avg < 0.8:
            self.momentum = "steady"
        else:
            self.momentum = "thriving"

    def suggest_mode(self, user_message: str) -> str:
        """Suggest a teaching mode based on context."""
        msg = user_message.lower()

        if any(w in msg for w in ["quiz", "test", "question"]):
            return "quiz"
        if any(w in msg for w in ["why", "how come", "explain why"]):
            return "socratic"
        if any(w in msg for w in ["review", "summary", "what did we cover"]):
            return "review"

        # Auto-switch to quiz after several explain interactions
        self.interaction_count += 1
        if self.interaction_count % 5 == 0 and self.mode == "explain":
            return "quiz"

        return self.mode

    def assess_level_change(self) -> str | None:
        """Check if the student should move to a different level.
        Returns new level or None if no change needed.
        """
        if len(self.recent_scores) < 3:
            return None

        avg = sum(self.recent_scores) / len(self.recent_scores)

        if self.level == "beginner" and avg >= 0.8 and self.quiz_count >= 3:
            return "intermediate"
        if self.level == "intermediate" and avg >= 0.85 and self.quiz_count >= 5:
            return "advanced"
        if self.level == "advanced" and avg < 0.4:
            return "intermediate"
        if self.level == "intermediate" and avg < 0.3:
            return "beginner"

        return None

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "momentum": self.momentum,
            "mode": self.mode,
            "recent_scores": self.recent_scores,
            "interaction_count": self.interaction_count,
            "quiz_count": self.quiz_count,
        }
