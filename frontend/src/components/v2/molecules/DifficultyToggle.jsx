import { Button } from "../atoms/Button";

export function DifficultyToggle({ options, selectedId, onSelect, className = "" }) {
  const containerClassName = [
    "inline-flex items-center justify-center rounded-full border border-white/10 bg-slate-950/45 p-1.5 shadow-[0_20px_45px_-30px_rgba(15,23,42,0.95)] backdrop-blur-sm",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div aria-label="Select difficulty" className={containerClassName}>
      {options.map((option) => {
        const isSelected = option.id === selectedId;
        const isOnlyOption = options.length === 1;

        return (
          <Button
            key={option.id}
            type="button"
            variant={isSelected ? "primary" : "secondary"}
            size="sm"
            className={[
              "min-w-[104px] rounded-none px-5",
              isOnlyOption ? "rounded-full" : "first:rounded-l-full first:rounded-r-none last:rounded-l-none last:rounded-r-full",
              isSelected ? "border-transparent" : "border-transparent bg-transparent hover:bg-white/[0.05]",
            ]
              .filter(Boolean)
              .join(" ")}
            onClick={() => onSelect(option.id)}
          >
            {option.label}
          </Button>
        );
      })}
    </div>
  );
}

export default DifficultyToggle;
