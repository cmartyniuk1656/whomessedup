export function FieldHint({ children }) {
  if (!children) {
    return null;
  }

  return <p className="mt-1 text-xs text-slate-400">{children}</p>;
}
