// One place that decides whether this device gets the lighter experience (no WebGL button light, no blur filters).
type Nav = Navigator & { deviceMemory?: number; connection?: { saveData?: boolean } };

export const isLowEnd = (): boolean => {
  if (typeof window === "undefined") return false; // server render and unit tests
  const n = navigator as Nav;
  return (
    (n.hardwareConcurrency ?? 8) <= 4 ||
    (n.deviceMemory ?? 8) <= 4 ||
    n.connection?.saveData === true ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
};

if (typeof document !== "undefined" && isLowEnd()) document.documentElement.classList.add("lite");
