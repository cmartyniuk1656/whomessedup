export const formatInt = (value) =>
  typeof value === "number" ? value.toLocaleString(undefined, { maximumFractionDigits: 0 }) : value;

export const formatFloat = (value, digits = 3) =>
  typeof value === "number"
    ? value.toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })
    : value;
