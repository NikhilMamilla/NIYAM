import { useLayoutEffect, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";

import "./GooeyNav.css";

// Original replacement for the copied React Bits "Gooey Nav" (see THIRD_PARTY_NOTICES.md): a pill behind
// the active item slides to it with a CSS transition. No WebGL, no canvas, no blob/particle physics.
export interface GooeyNavItem {
  label: string;
  icon?: ReactNode;
}

export interface GooeyNavProps {
  items?: GooeyNavItem[];
  activeIndex?: number;
  onChange?: (index: number, item: GooeyNavItem) => void;
  theme?: "dark" | "light";
  size?: "sm" | "md" | "lg";
  frame?: boolean;
  className?: string;
  style?: CSSProperties;
}

const THEMES = {
  dark: {
    "--gn-frame": "rgba(38, 35, 46, 0.66)",
    "--gn-frame-edge": "rgba(255, 255, 255, 0.08)",
    "--gn-frame-highlight": "rgba(255, 255, 255, 0.07)",
    "--gn-frame-shadow": "0 22px 44px -20px rgba(0, 0, 0, 0.8), 0 6px 16px -8px rgba(0, 0, 0, 0.5)",
    "--gn-ink": "#f4f4f5",
    "--gn-muted": "rgba(244, 244, 245, 0.62)",
    "--gn-pill": "rgba(255, 255, 255, 0.08)",
  },
  light: {
    "--gn-frame": "rgba(240, 240, 243, 0.8)",
    "--gn-frame-edge": "rgba(24, 24, 27, 0.07)",
    "--gn-frame-highlight": "rgba(255, 255, 255, 0.95)",
    "--gn-frame-shadow": "0 22px 44px -22px rgba(24, 24, 27, 0.3), 0 6px 16px -10px rgba(24, 24, 27, 0.16)",
    "--gn-ink": "#27272a",
    "--gn-muted": "rgba(39, 39, 42, 0.62)",
    "--gn-pill": "rgba(24, 24, 27, 0.06)",
  },
} as const;

const SIZES = { sm: "gooey-nav--sm", md: "gooey-nav--md", lg: "gooey-nav--lg" } as const;

export default function GooeyNav({
  items = [],
  activeIndex = 0,
  onChange,
  theme = "dark",
  size = "md",
  frame = true,
  className = "",
  style,
}: GooeyNavProps) {
  const listRef = useRef<HTMLUListElement>(null);
  const pillRef = useRef<HTMLSpanElement>(null);
  const [ready, setReady] = useState(false);

  useLayoutEffect(() => {
    const move = () => {
      const list = listRef.current;
      const pill = pillRef.current;
      const item = list?.children[activeIndex];
      if (!list || !pill || !(item instanceof HTMLElement)) return;
      pill.style.transform = `translate(${item.offsetLeft}px, ${item.offsetTop}px)`;
      pill.style.width = `${item.offsetWidth}px`;
      pill.style.height = `${item.offsetHeight}px`;
      setReady(true);
    };
    move();
    const list = listRef.current;
    if (!list) return;
    const ro = new ResizeObserver(move);
    ro.observe(list);
    return () => ro.disconnect();
  }, [activeIndex, items.length, size]);

  const palette = theme === "light" ? "light" : "dark";

  return (
    <nav
      className={`gooey-nav ${SIZES[size] ?? SIZES.md}${frame ? " gooey-nav--framed" : ""} ${className}`.trim()}
      style={{ ...THEMES[palette], ...style } as CSSProperties}
    >
      {frame && <span className="gooey-nav__rim" />}
      <div className="gooey-nav__stage">
        <span ref={pillRef} className="gooey-nav__pill" style={{ opacity: ready ? 1 : 0 }} aria-hidden="true" />
        <ul ref={listRef} className="gooey-nav__list">
          {items.map((item, index) => (
            <li key={`${item.label}-${index}`} className="gooey-nav__item" data-active={index === activeIndex ? "" : undefined}>
              <button
                type="button"
                className="gooey-nav__link"
                aria-current={index === activeIndex ? "page" : undefined}
                onClick={() => onChange?.(index, item)}
              >
                {item.icon && <span className="gooey-nav__icon">{item.icon}</span>}
                {item.label && <span className="gooey-nav__label">{item.label}</span>}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  );
}
