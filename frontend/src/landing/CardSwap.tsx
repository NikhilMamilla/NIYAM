import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";

import "./CardSwap.css";

// Original replacement for the copied React Bits "Card Swap" (see THIRD_PARTY_NOTICES.md): each card's
// position in the stack is a CSS transform computed from its index in an `order` array; reordering the
// array (on autoplay, click, drag or an arrow key) just changes that transform, and the existing CSS
// transition on `.card-swap-slot` animates the move. No requestAnimationFrame loop, no spring physics.
export interface CardSwapItem {
  title?: string;
  image?: string;
  icon?: ReactNode;
  alt?: string;
}

export interface CardSwapHandle {
  next: () => void;
  prev: () => void;
}

export interface CardSwapProps {
  items?: CardSwapItem[];
  width?: number;
  height?: number;
  cardDistance?: number;
  verticalDistance?: number;
  depth?: number;
  skewAmount?: number;
  visibleCards?: number;
  delay?: number;
  autoplay?: boolean;
  pauseOnHover?: boolean;
  draggable?: boolean;
  cardRadius?: number;
  theme?: "dark" | "light";
  onChange?: (index: number) => void;
  className?: string;
  style?: CSSProperties;
}

const THEMES = {
  dark: {
    "--swap-tile": "linear-gradient(180deg, #3a3644 0%, #27242f 100%)",
    "--swap-tile-edge": "rgba(255, 255, 255, 0.07)",
    "--swap-tile-highlight": "rgba(255, 255, 255, 0.12)",
    "--swap-shadow": "0 30px 60px -24px rgba(0, 0, 0, 0.8), 0 10px 24px -12px rgba(0, 0, 0, 0.55)",
    "--swap-media-edge": "rgba(255, 255, 255, 0.06)",
    "--swap-ink": "#f4f4f5",
    "--swap-badge": "rgba(255, 255, 255, 0.08)",
    "--swap-shade": "#100e15",
  },
  light: {
    "--swap-tile": "linear-gradient(180deg, #ffffff 0%, #f6f6f8 100%)",
    "--swap-tile-edge": "rgba(24, 24, 27, 0.08)",
    "--swap-tile-highlight": "rgba(255, 255, 255, 1)",
    "--swap-shadow": "0 30px 60px -28px rgba(24, 24, 27, 0.35), 0 10px 24px -14px rgba(24, 24, 27, 0.2)",
    "--swap-media-edge": "rgba(24, 24, 27, 0.06)",
    "--swap-ink": "#27272a",
    "--swap-badge": "rgba(24, 24, 27, 0.05)",
    "--swap-shade": "#ffffff",
  },
} as const;

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value));
const DRAG_THRESHOLD = 60;

const CardSwap = forwardRef<CardSwapHandle, CardSwapProps>(function CardSwap(
  {
    items = [],
    width = 460,
    height = 340,
    cardDistance = 60,
    verticalDistance = 70,
    depth = 90,
    skewAmount = 6,
    visibleCards = 4,
    delay = 4000,
    autoplay = true,
    pauseOnHover = true,
    draggable = true,
    cardRadius = 18,
    theme = "dark",
    onChange,
    className = "",
    style,
  },
  ref,
) {
  const count = items.length;
  const [order, setOrder] = useState<number[]>(() => items.map((_, i) => i));
  const [hovered, setHovered] = useState(false);
  const drag = useRef<{ x: number; dragging: boolean } | null>(null);
  const frontRef = useRef<HTMLDivElement | null>(null);

  // Keep the order array the same length as items (e.g. when DEMO is edited), front card first.
  useEffect(() => {
    setOrder((prev) => {
      if (prev.length === count && prev.every((i) => i < count)) return prev;
      return items.map((_, i) => i);
    });
  }, [count, items]);

  const next = () => setOrder((o) => (o.length < 2 ? o : [...o.slice(1), o[0]!]));
  const prev = () => setOrder((o) => (o.length < 2 ? o : [o[o.length - 1]!, ...o.slice(0, -1)]));
  const goTo = (position: number) => setOrder((o) => [...o.slice(position), ...o.slice(0, position)]);

  useImperativeHandle(ref, () => ({ next, prev }), []);

  useEffect(() => {
    onChange?.(order[0] ?? 0);
  }, [order, onChange]);

  const visible = clamp(Math.round(visibleCards), 1, Math.max(1, count));

  // Autoplay, restarted whenever the order changes so every step gets the full delay.
  useEffect(() => {
    if (!autoplay || count < 2 || (pauseOnHover && hovered)) return;
    const id = window.setTimeout(next, Math.max(400, delay));
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [order, autoplay, pauseOnHover, hovered, delay, count]);

  // A generous, padded container for the stepped-and-skewed stack (not the original's exact bounding box).
  const skewPad = width * Math.tan((Math.abs(skewAmount) * Math.PI) / 180);
  const stageW = Math.ceil(width + Math.max(0, visible - 1) * cardDistance + 64);
  const stageH = Math.ceil(height + Math.max(0, visible - 1) * verticalDistance + skewPad + 64);
  const originX = 32 + width / 2;
  const originY = stageH - 32 - height / 2;

  const rootStyle = useMemo(() => {
    // Built as a plain Record first and spread (not written as literal keys) into the final cast: a custom
    // property directly inside an object literal asserted "as CSSProperties" fails the excess-property
    // check (csstype's Properties has no index signature), but one contributed by a spread does not.
    const vars: Record<string, string> = {
      ...THEMES[theme === "light" ? "light" : "dark"],
      "--swap-w": `${width}px`,
      "--swap-h": `${height}px`,
      "--swap-ox": `${originX}px`,
      "--swap-oy": `${originY}px`,
      "--swap-stage-w": `${stageW}px`,
      "--swap-stage-h": `${stageH}px`,
      "--swap-ratio": `${stageW} / ${stageH}`,
      "--swap-radius": `${Math.max(0, cardRadius)}px`,
    };
    return { ...vars, ...style } as CSSProperties;
  }, [theme, width, height, originX, originY, stageW, stageH, cardRadius, style]);

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      next();
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      prev();
    }
  };

  const onPointerDown = (event: React.PointerEvent, itemIndex: number) => {
    if (!draggable || order[0] !== itemIndex) return;
    drag.current = { x: event.clientX, dragging: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: React.PointerEvent) => {
    const d = drag.current;
    const front = frontRef.current;
    if (!d || !front) return;
    const dx = event.clientX - d.x;
    if (!d.dragging && Math.abs(dx) < 4) return;
    d.dragging = true;
    front.style.transition = "none";
    front.style.transform = `translate3d(${dx}px, 0, 0) skewY(${skewAmount}deg)`;
  };
  const endDrag = (event: React.PointerEvent) => {
    const d = drag.current;
    const front = frontRef.current;
    drag.current = null;
    if (!d?.dragging || !front) return;
    front.style.transition = "";
    front.style.transform = "";
    const dx = event.clientX - d.x;
    if (Math.abs(dx) > DRAG_THRESHOLD) (dx < 0 ? next : prev)();
  };

  return (
    <div
      className={`card-swap${className ? ` ${className}` : ""}`}
      style={rootStyle}
      tabIndex={0}
      role="region"
      aria-roledescription="carousel"
      aria-label="Card stack"
      onKeyDown={onKeyDown}
      onPointerEnter={() => setHovered(true)}
      onPointerLeave={() => setHovered(false)}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
    >
      <div className="card-swap-sizer" aria-hidden="true">
        <span />
      </div>
      <div className="card-swap-stage">
        {items.map((item, itemIndex) => {
          const position = order.indexOf(itemIndex);
          const onStage = position >= 0 && position < visible;
          const p = position < 0 ? count : position;
          const transform = `translate3d(${p * cardDistance}px, ${-p * verticalDistance}px, ${-p * depth}px) skewY(${skewAmount}deg)`;
          return (
            <div
              key={itemIndex}
              ref={position === 0 ? frontRef : undefined}
              className="card-swap-slot"
              data-swap-index={itemIndex}
              data-front={position === 0 ? "" : undefined}
              style={{
                transform,
                opacity: onStage ? 1 : 0,
                zIndex: count - p,
                pointerEvents: onStage ? "auto" : "none",
                cursor: position === 0 ? (draggable ? "grab" : "") : "pointer",
              }}
              onPointerDown={(e) => onPointerDown(e, itemIndex)}
              onClick={() => onStage && position > 0 && goTo(position)}
            >
              <div className="card-swap-card">
                <div className="card-swap-item">
                  {(item.icon || item.title) && (
                    <div className="card-swap-head">
                      {item.icon && <span className="card-swap-icon">{item.icon}</span>}
                      {item.title && <span className="card-swap-title">{item.title}</span>}
                    </div>
                  )}
                  {item.image && (
                    <div className="card-swap-media">
                      <img src={item.image} alt={item.alt ?? item.title ?? ""} draggable={false} />
                    </div>
                  )}
                </div>
                <span className="card-swap-card-rim" aria-hidden="true" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
});

export default CardSwap;
