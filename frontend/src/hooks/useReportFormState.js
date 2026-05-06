import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { buildInitialReportValues } from "../utils/reportFormValues";

export function useReportFormState(reports) {
  const [selectedReportId, setSelectedReportId] = useState("");
  const [formValues, setFormValues] = useState({});
  const pendingFormValuesRef = useRef(null);

  useEffect(() => {
    if (!reports.length) {
      if (selectedReportId) {
        setSelectedReportId("");
      }
      return;
    }
    const hasSelectedReport = reports.some((report) => report.id === selectedReportId);
    if (selectedReportId && !hasSelectedReport) {
      setSelectedReportId("");
    }
  }, [reports, selectedReportId]);

  const selectedReport = useMemo(
    () => reports.find((report) => report.id === selectedReportId) ?? null,
    [reports, selectedReportId]
  );

  useEffect(() => {
    if (!selectedReport) {
      setFormValues({});
      return;
    }
    if (pendingFormValuesRef.current) {
      setFormValues(pendingFormValuesRef.current);
      pendingFormValuesRef.current = null;
      return;
    }
    setFormValues(buildInitialReportValues(selectedReport));
  }, [selectedReport]);

  const setReportFormValues = useCallback((reportId, values) => {
    pendingFormValuesRef.current = values ?? {};
    setSelectedReportId(reportId);
    setFormValues(values ?? {});
  }, []);

  const handleValueChange = (fieldId, value) => {
    setFormValues((current) => ({ ...current, [fieldId]: value }));
  };

  const handleMultiTextChange = (fieldId, index, value) => {
    setFormValues((current) => {
      const next = Array.isArray(current[fieldId]) ? [...current[fieldId]] : [""];
      while (next.length <= index) {
        next.push("");
      }
      next[index] = value;
      return { ...current, [fieldId]: next };
    });
  };

  const handleAddMultiTextRow = (fieldId) => {
    setFormValues((current) => {
      const next = Array.isArray(current[fieldId]) ? [...current[fieldId]] : [""];
      next.push("");
      return { ...current, [fieldId]: next };
    });
  };

  const handleRemoveMultiTextRow = (fieldId, index) => {
    setFormValues((current) => {
      const next = Array.isArray(current[fieldId]) ? [...current[fieldId]] : [""];
      if (next.length <= 1) {
        return { ...current, [fieldId]: [""] };
      }
      next.splice(index, 1);
      return { ...current, [fieldId]: next.length ? next : [""] };
    });
  };

  return {
    selectedReportId,
    selectedReport,
    formValues,
    setSelectedReportId,
    setReportFormValues,
    handleValueChange,
    handleMultiTextChange,
    handleAddMultiTextRow,
    handleRemoveMultiTextRow,
  };
}
