import belorenChildOfAlarArt from "../assets/boss-card-art/beloren-child-of-alar.png";
import chimaerusTheUndreamtGodArt from "../assets/boss-card-art/chimaerus-the-undreamt-god.png";
import crownOfTheCosmosArt from "../assets/boss-card-art/crown-of-the-cosmos.png";
import fallenKingSalhadaarArt from "../assets/boss-card-art/fallen-king-salhadaar.png";
import imperatorAverzianArt from "../assets/boss-card-art/imperator-aversian.png";
import lightblindedVanguardArt from "../assets/boss-card-art/lightblinded-vanguard.png";
import midnightFallsArt from "../assets/boss-card-art/midnight-falls.png";
import vaelgorAndEzzorakArt from "../assets/boss-card-art/vaelgor-and-ezzorak.png";
import vorasiusArt from "../assets/boss-card-art/vorasius.png";

export const REPORT_DIFFICULTY_OPTIONS = [
  { id: "heroic", label: "Heroic" },
  { id: "mythic", label: "Mythic" },
];

export const DEFAULT_REPORT_DIFFICULTY = "mythic";

export const MIDNIGHT_SEASON_ONE_FIGHTS = [
  { id: "imperator-averzian", title: "Imperator Averzian", art: imperatorAverzianArt },
  { id: "vorasius", title: "Vorasius", art: vorasiusArt },
  { id: "fallen-king-salhadaar", title: "Fallen-King Salhadaar", art: fallenKingSalhadaarArt },
  { id: "vaelgor-and-ezzorak", title: "Vaelgor & Ezzorak", art: vaelgorAndEzzorakArt },
  { id: "lightblinded-vanguard", title: "Lightblinded Vanguard", art: lightblindedVanguardArt },
  { id: "crown-of-the-cosmos", title: "Crown of the Cosmos", art: crownOfTheCosmosArt },
  { id: "chimaerus-the-undreamt-god", title: "Chimaerus, the Undreamt God", art: chimaerusTheUndreamtGodArt },
  { id: "beloren-child-of-alar", title: "Belo'ren, Child of Al'ar", art: belorenChildOfAlarArt },
  { id: "midnight-falls", title: "Midnight Falls", art: midnightFallsArt },
];
