import { MIDNIGHT_SEASON_ONE_FIGHTS } from "./midnightSeasonOne";
import { MIDNIGHT_SEASON_TWO_FIGHTS } from "./midnightSeasonTwo";

// Central raid catalog for boss browsing and cached-report fight restoration.
export const DEFAULT_MIDNIGHT_RAID_ID = "season-2-venomous-abyss";

export const MIDNIGHT_RAIDS = [
  {
    id: "season-1-voidspire",
    label: "Season 1: Voidspire",
    fights: MIDNIGHT_SEASON_ONE_FIGHTS,
  },
  {
    id: "season-2-venomous-abyss",
    label: "Season 2: Venomous Abyss",
    fights: MIDNIGHT_SEASON_TWO_FIGHTS,
  },
];

export function getMidnightRaidIdForFight(fightId) {
  return MIDNIGHT_RAIDS.find((raid) => raid.fights.some((fight) => fight.id === fightId))?.id ?? null;
}
