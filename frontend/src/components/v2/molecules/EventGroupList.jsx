import { Tooltip } from "../atoms/Tooltip";

const CHILD_TONE_CLASSES = {
  danger: {
    row: "border-rose-300/35 bg-rose-400/10 text-rose-100",
    label: "font-semibold text-rose-200",
  },
  success: {
    row: "border-emerald-300/25 bg-emerald-400/10 text-emerald-100",
    label: "font-semibold text-emerald-200",
  },
  warning: {
    row: "border-amber-300/25 bg-amber-400/10 text-amber-100",
    label: "font-semibold text-amber-100",
  },
  default: {
    row: "border-white/10 bg-slate-950/25 text-slate-300",
    label: "font-semibold text-slate-200",
  },
};

const CONSUMABLE_STATUS_CLASSES = {
  success: {
    icon: "border-emerald-300/40 bg-emerald-400/10 text-emerald-200",
    status: "text-emerald-200",
  },
  danger: {
    icon: "border-rose-300/40 bg-rose-400/10 text-rose-200",
    status: "text-rose-200",
  },
  default: {
    icon: "border-slate-500/40 bg-slate-700/20 text-slate-300",
    status: "text-slate-300",
  },
};

const DETAIL_ITEM_TONE_CLASSES = {
  danger: {
    item: "",
    label: "font-semibold text-rose-300",
    timestamp: "ml-1 text-slate-300",
    description: "ml-1 text-rose-100",
    ability: "ml-1 font-semibold text-slate-100 underline decoration-dotted underline-offset-2 hover:text-rose-200",
    abilityText: "ml-1 font-semibold text-slate-100",
    badge: "border-rose-300/35 bg-rose-400/10 text-rose-100",
  },
  muted: {
    item: "opacity-60",
    label: "font-semibold text-slate-400",
    timestamp: "ml-1 text-slate-500",
    description: "ml-1 text-slate-500",
    ability: "ml-1 font-semibold text-slate-400 underline decoration-dotted underline-offset-2 hover:text-slate-300",
    abilityText: "ml-1 font-semibold text-slate-400",
    badge: "border-slate-500/25 bg-slate-500/10 text-slate-400",
  },
  success: {
    item: "",
    label: "font-semibold text-emerald-300",
    timestamp: "ml-1 text-slate-300",
    description: "ml-1 text-slate-200",
    ability: "ml-1 font-semibold text-slate-100 underline decoration-dotted underline-offset-2 hover:text-emerald-200",
    abilityText: "ml-1 font-semibold text-slate-100",
    badge: "border-emerald-300/35 bg-emerald-400/10 text-emerald-100",
  },
  warning: {
    item: "",
    label: "font-semibold text-amber-200",
    timestamp: "ml-1 text-slate-300",
    description: "ml-1 text-amber-50",
    ability: "ml-1 font-semibold text-slate-100 underline decoration-dotted underline-offset-2 hover:text-amber-200",
    abilityText: "ml-1 font-semibold text-slate-100",
    badge: "border-amber-300/35 bg-amber-400/10 text-amber-100",
  },
  default: {
    item: "",
    label: "font-semibold text-emerald-300",
    timestamp: "ml-1 text-slate-300",
    description: "ml-1 text-slate-200",
    ability: "ml-1 font-semibold text-slate-100 underline decoration-dotted underline-offset-2 hover:text-emerald-200",
    abilityText: "ml-1 font-semibold text-slate-100",
    badge: "border-amber-300/30 bg-amber-300/10 text-amber-100",
  },
};

function CheckIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true" focusable="false">
      <path d="M3.25 8.15 6.45 11.25 12.8 4.75" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" aria-hidden="true" focusable="false">
      <path d="M4.5 4.5 11.5 11.5M11.5 4.5 4.5 11.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function AbilityTooltipContent({ description, tags = [] }) {
  return (
    <span className="block max-w-80 space-y-2">
      {description ? <span className="block text-slate-100">{description}</span> : null}
      {tags.length ? (
        <span className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex rounded-full border border-amber-300/30 bg-amber-300/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-100"
            >
              {tag}
            </span>
          ))}
        </span>
      ) : null}
    </span>
  );
}

function AbilityText({ child }) {
  if (!child.abilityLabel) {
    return null;
  }

  const toneClasses = DETAIL_ITEM_TONE_CLASSES[child.tone] || DETAIL_ITEM_TONE_CLASSES.default;
  const tooltipBadges = child.tooltipBadges || child.badges || [];
  const hasTooltip = Boolean(child.tooltip || tooltipBadges.length);
  const content = child.abilityHref ? (
    <a
      href={child.abilityHref}
      target="_blank"
      rel="noreferrer"
      className={toneClasses.ability}
      onClick={(event) => event.stopPropagation()}
    >
      {child.abilityLabel}
    </a>
  ) : (
    <span className={toneClasses.abilityText}>{child.abilityLabel}</span>
  );

  if (!hasTooltip) {
    return content;
  }

  return (
    <Tooltip
      content={<AbilityTooltipContent description={child.tooltip} tags={tooltipBadges} />}
      placement="right"
      triggerClassName="align-middle"
    >
      {content}
    </Tooltip>
  );
}

function ConsumableChildItem({ child }) {
  const toneClasses = CONSUMABLE_STATUS_CLASSES[child.tone] || CONSUMABLE_STATUS_CLASSES.default;
  const isUsed = child.description === "used" || child.tone === "success";

  return (
    <li className="list-none px-1 py-1">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
        <span className={`inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${toneClasses.icon}`}>
          {isUsed ? <CheckIcon /> : <XIcon />}
        </span>
        <Tooltip content={child.tooltip} placement="right" triggerClassName="align-middle">
          <span className="font-semibold text-slate-200 underline decoration-dotted underline-offset-2 hover:text-slate-100">
            {child.label}
          </span>
        </Tooltip>
        {child.description ? <span className={toneClasses.status}>{child.description}</span> : null}
      </div>
    </li>
  );
}

function DetailItemBadges({ item }) {
  if (!item.badges?.length) {
    return null;
  }

  const toneClasses = DETAIL_ITEM_TONE_CLASSES[item.tone] || DETAIL_ITEM_TONE_CLASSES.default;

  return (
    <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
      {item.badges.map((badge) => (
        <span
          key={`${item.id}-${badge}`}
          className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ${toneClasses.badge}`}
        >
          {badge}
        </span>
      ))}
    </div>
  );
}

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
            {group.items.map((item) => {
              const toneClasses = DETAIL_ITEM_TONE_CLASSES[item.tone] || DETAIL_ITEM_TONE_CLASSES.default;
              return (
                <li key={item.id} className={toneClasses.item}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <span className={toneClasses.label}>{item.label}</span>
                      {item.timestampLabel ? <span className={toneClasses.timestamp}>{item.timestampLabel}</span> : null}
                      <AbilityText child={item} />
                      {item.description ? <span className={toneClasses.description}>{item.description}</span> : null}
                    </div>
                    <DetailItemBadges item={item} />
                  </div>
                  {item.children?.length ? (
                    <ul className="mt-2 ml-1 space-y-1.5 border-l border-white/10 pl-3">
                      {item.children.map((child) => {
                        if (child.kind === "consumable") {
                          return <ConsumableChildItem key={child.id} child={child} />;
                        }
                        const toneClasses = CHILD_TONE_CLASSES[child.tone] || CHILD_TONE_CLASSES.default;
                        return (
                          <li
                            key={child.id}
                            className={[
                              "list-none rounded-md border px-3 py-2",
                              toneClasses.row,
                            ]
                              .filter(Boolean)
                              .join(" ")}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0 flex-1">
                                <span className={toneClasses.label}>{child.label}</span>
                                {child.timestampLabel ? <span className="ml-1 text-slate-400">{child.timestampLabel}</span> : null}
                                <AbilityText child={child} />
                                {child.description ? <span className="ml-1 text-slate-100">{child.description}</span> : null}
                              </div>
                              {child.badges?.length ? (
                                <DetailItemBadges item={child} />
                              ) : null}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
