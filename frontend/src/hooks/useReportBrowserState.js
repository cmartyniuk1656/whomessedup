import { useMemo, useState } from "react";
import {
  DEFAULT_REPORT_DIFFICULTY,
  REPORT_DIFFICULTY_OPTIONS,
} from "../config/midnightSeasonOne";
import { DEFAULT_MIDNIGHT_RAID_ID, MIDNIGHT_RAIDS } from "../config/midnightRaids";
import { useReportFormState } from "./useReportFormState";

export function useReportBrowserState(reports) {
  const [selectedRaidId, setSelectedRaidId] = useState(DEFAULT_MIDNIGHT_RAID_ID);
  const [selectedDifficulty, setSelectedDifficulty] = useState(DEFAULT_REPORT_DIFFICULTY);
  const [selectedFightId, setSelectedFightId] = useState("");

  const selectedRaid = useMemo(
    () => MIDNIGHT_RAIDS.find((raid) => raid.id === selectedRaidId) ?? MIDNIGHT_RAIDS[0],
    [selectedRaidId]
  );

  const fightOptions = selectedRaid.fights;

  const selectedFight = useMemo(
    () => fightOptions.find((fight) => fight.id === selectedFightId) ?? null,
    [fightOptions, selectedFightId]
  );

  const selectedDifficultyOption = useMemo(
    () => REPORT_DIFFICULTY_OPTIONS.find((option) => option.id === selectedDifficulty) ?? REPORT_DIFFICULTY_OPTIONS[0],
    [selectedDifficulty]
  );

  const reportCountsByFightId = useMemo(() => {
    const counts = {};
    fightOptions.forEach((fight) => {
      counts[fight.id] = 0;
    });

    reports.forEach((report) => {
      if (report?.fightId && report?.difficulty === selectedDifficulty && Object.prototype.hasOwnProperty.call(counts, report.fightId)) {
        counts[report.fightId] += 1;
      }
    });

    return counts;
  }, [fightOptions, reports, selectedDifficulty]);

  const availableReports = useMemo(() => {
    if (!selectedFightId) {
      return [];
    }

    return reports.filter((report) => report?.fightId === selectedFightId && report?.difficulty === selectedDifficulty);
  }, [reports, selectedDifficulty, selectedFightId]);

  const formState = useReportFormState(availableReports);

  return {
    raidOptions: MIDNIGHT_RAIDS,
    selectedRaidId,
    setSelectedRaidId,
    fightOptions,
    difficultyOptions: REPORT_DIFFICULTY_OPTIONS,
    selectedDifficulty,
    selectedDifficultyLabel: selectedDifficultyOption?.label ?? selectedDifficulty,
    setSelectedDifficulty,
    selectedFightId,
    selectedFight,
    setSelectedFightId,
    reportCountsByFightId,
    availableReports,
    ...formState,
  };
}
