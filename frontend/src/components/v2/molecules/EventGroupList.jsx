export function EventGroupList({ details }) {
  if (!details?.groups?.length) {
    return null;
  }

  return (
    <div className="space-y-3">
      {details.groups.map((group) => (
        <div
          key={group.id}
          className="rounded-[18px] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.015))] px-4 py-3.5 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]"
        >
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            {group.link ? (
              <a
                href={group.link}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-semibold text-emerald-300 underline decoration-dotted underline-offset-2 hover:text-emerald-200"
              >
                {group.title}
              </a>
            ) : (
              <p className="text-sm font-semibold text-slate-100">{group.title}</p>
            )}
            {group.subtitle ? <p className="text-xs text-slate-400">{group.subtitle}</p> : null}
          </div>
          <ul className="mt-3 ml-5 list-disc space-y-1.5 text-sm text-slate-300">
            {group.items.map((item) => (
              <li key={item.id}>
                <span className="font-semibold text-emerald-300">{item.label}</span>
                {item.timestampLabel ? <span className="ml-1 text-slate-300">{item.timestampLabel}</span> : null}
                {item.description ? <span className="ml-1 text-slate-200">{item.description}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
