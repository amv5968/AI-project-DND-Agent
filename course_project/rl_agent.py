from collections import defaultdict
import random
from typing import Dict, List, Optional, Tuple

TEMPERATURE_OPTIONS = [0.2, 0.4, 0.6, 0.8]

GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY = 0.999


class DMRLAgent:
    def __init__(self):
        self.Q: Dict[Tuple, float] = defaultdict(float)
        self.returns_count: Dict[Tuple, int] = defaultdict(int)
        self.epsilon: float = EPSILON_START
        self._episode: List[Tuple] = []
        self._pending: Optional[Tuple] = None

    def _encode_state(self, scenario: str, turn_count: int) -> Tuple[str, int]:
        return (scenario, min(turn_count // 3, 5))

    def choose_temperature(self, scenario: str, turn_count: int) -> float:
        state = self._encode_state(scenario, turn_count)
        n = len(TEMPERATURE_OPTIONS)
        if random.random() < self.epsilon:
            action = random.randrange(n)
        else:
            q_vals = [self.Q[(state, a)] for a in range(n)]
            max_q = max(q_vals)
            bests = [a for a in range(n) if self.Q[(state, a)] == max_q]
            action = random.choice(bests)
        self._pending = (state, action)
        return TEMPERATURE_OPTIONS[action]

    def record_reward(self, reward: float) -> None:
        if self._pending is not None:
            state, action = self._pending
            self._episode.append((state, action, reward))
            self._pending = None

    def end_session(self) -> None:
        self._update_from_episode(self._episode)
        self._episode = []
        self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)

    def _update_from_episode(self, episode: List[Tuple]) -> None:
        G = 0.0
        visited = set()
        for t in range(len(episode) - 1, -1, -1):
            state, action, reward = episode[t]
            G = reward + GAMMA * G
            if (state, action) not in visited:
                visited.add((state, action))
                self.returns_count[(state, action)] += 1
                self.Q[(state, action)] += (
                    (G - self.Q[(state, action)]) / self.returns_count[(state, action)]
                )
