import { useMemo, useState } from "react";
import {
  DEFAULT_REPORT_DIFFICULTY,
  MIDNIGHT_SEASON_ONE_FIGHTS,
  REPORT_DIFFICULTY_OPTIONS,
} from "../config/midnightSeasonOne";
import { useReportFormState } from "./useReportFormState";

export function useReportBrowserState(reports) {
  const [selectedDifficulty, setSelectedDifficulty] = useState(DEFAULT_REPORT_DIFFICULTY);
  const [selectedFightId, setSelectedFightId] = useState("");

  const selectedFight = useMemo(
    () => MIDNIGHT_SEASON_ONE_FIGHTS.find((fight) => fight.id === selectedFightId) ?? null,
    [selectedFightId]
  );

  const selectedDifficultyOption = useMemo(
    () => REPORT_DIFFICULTY_OPTIONS.find((option) => option.id === selectedDifficulty) ?? REPORT_DIFFICULTY_OPTIONS[0],
    [selectedDifficulty]
  );

  const reportCountsByFightId = useMemo(() => {
    const counts = {};
    MIDNIGHT_SEASON_ONE_FIGHTS.forEach((fight) => {
      counts[fight.id] = 0;
    });

    reports.forEach((report) => {
      if (report?.fightId && report?.difficulty === selectedDifficulty && Object.prototype.hasOwnProperty.call(counts, report.fightId)) {
        counts[report.fightId] += 1;
      }
    });

    return counts;
  }, [reports, selectedDifficulty]);

  const availableReports = useMemo(() => {
    if (!selectedFightId) {
      return [];
    }

    return reports.filter((report) => report?.fightId === selectedFightId && report?.difficulty === selectedDifficulty);
  }, [reports, selectedDifficulty, selectedFightId]);

  const formState = useReportFormState(availableReports);

  return {
    fightOptions: MIDNIGHT_SEASON_ONE_FIGHTS,
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
