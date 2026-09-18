"""Per-pull access to scoped event streams and shared mechanics evidence rows."""
from dataclasses import dataclass

from .mechanics_events import ability, aura_lives
from .mechanics_models import MechanicSet


@dataclass
class PullContext:
    code: str
    fight: object
    pull_index: int
    streams: dict
    names: dict
    owners: dict

    @property
    def players(self):
        return set(self.fight.friendly_player_ids)

    def events(self, stream, ids=None, *, friendly=False):
        return [e for e in self.streams.get(stream, [])
                if (ids is None or ability(e) in ids)
                and (not friendly or e.get("targetID") in self.players)]

    def name(self, actor_id):
        return self.names.get(actor_id, f"Player {actor_id}")

    def row(self, start, index, label):
        return MechanicSet(self.code, self.fight.id, self.pull_index,
                           self.fight.start, start, index, label)

    def offset(self, at):
        seconds = max(0, (at - self.fight.start) / 1000)
        return f"{int(seconds // 60)}:{seconds % 60:05.2f}"

    def lives(self, ids):
        return aura_lives(self.events("debuffs", ids), ids, self.players)

