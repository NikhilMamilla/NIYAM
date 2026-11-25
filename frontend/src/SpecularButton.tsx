import type { ComponentType, CSSProperties, ReactNode } from "react";

import "./SpecularButton.css";

// Original replacement for the copied React Bits "Specular Button" (see THIRD_PARTY_NOTICES.md): a CSS
// radial-gradient ring, masked down to just the border, animates an ambient light around the edge and
// brightens on hover/focus. No WebGL, no canvas, no pointer tracking. Same class names as before, so the
// rest of the project's CSS (segmented groups, the two-up button row, dashboard toolbars, ...) is untouched.
export interface SpecularButtonProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  as?: string | ComponentType<any>;
  size?: "sm" | "md" | "lg";
  radius?: number;
  tint?: string;
  tintOpacity?: number;
  textColor?: string;
  lineColor?: string;
  baseColor?: string;
  disabled?: boolean;
  className?: string;
  type?: string;
  style?: CSSProperties;
  children?: ReactNode;
  [key: string]: unknown;
}

export default function SpecularButton({
  as: Tag = "button",
  children,
  size = "lg",
  radius = 18,
  tint = "#ffffff",
  tintOpacity = 0.04,
  textColor = "#f5f5f5",
  lineColor = "#ffffff",
  baseColor = "#525252",
  disabled = false,
  className = "",
  type = "button",
  style,
  ...rest
}: SpecularButtonProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Comp = Tag as any;
  const native = Tag === "button";
  return (
    <Comp
      {...(native ? { type, disabled } : { "aria-disabled": disabled || undefined })}
      className={`specular-button specular-button--${size}${className ? ` ${className}` : ""}`}
      style={{
        "--sb-radius": `${radius}px`,
        "--sb-tint": tint,
        "--sb-tint-opacity": tintOpacity,
        "--sb-text-color": textColor,
        "--sb-line-color": lineColor,
        "--sb-base-color": baseColor,
        ...style,
      } as CSSProperties}
      {...rest}
    >
      <span className="specular-button__label">{children}</span>
    </Comp>
  );
}
