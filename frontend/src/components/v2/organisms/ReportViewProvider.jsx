/** Scope shareable controls to one loaded report without propagating every control update. */
import { useContext, useMemo, useState } from "react";
import { ViewContext, ScopeContext } from "../../../hooks/reportViewContext";
import { buildReportViewUrl, readReportView } from "../../../utils/reportShareLink";

export function ReportViewProvider({ shareUrl, children }) {
  const [registry] = useState(() => ({ saved: readReportView(shareUrl), active: new Map() }));
  const value = useMemo(() => ({
    registry,
    share: (url) => buildReportViewUrl(url, Object.fromEntries(
      [...registry.active].map(([key, read]) => [key, read()]),
    )),
  }), [registry]);
  return <ViewContext.Provider value={value}>{children}</ViewContext.Provider>;
}

export function ReportViewScope({ name, children }) {
  const parent = useContext(ScopeContext);
  return <ScopeContext.Provider value={`${parent}/${name}`}>{children}</ScopeContext.Provider>;
}
