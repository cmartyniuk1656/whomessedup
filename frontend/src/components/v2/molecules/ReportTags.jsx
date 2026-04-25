import { KeyValuePill } from "../atoms/KeyValuePill";

export function ReportTags({ tags }) {
  if (!tags?.length) {
    return null;
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {tags.map((tag) => (
        <KeyValuePill key={tag.id} label={tag.label} value={tag.value} />
      ))}
    </div>
  );
}
