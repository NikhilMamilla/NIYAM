import type { ComponentType, ReactElement } from "react";

export interface SpecularButtonProps {
  as?: string | ComponentType<any>;
  size?: "sm" | "md" | "lg";
  radius?: number;
  tint?: string;
  tintOpacity?: number;
  textColor?: string;
  lineColor?: string;
  baseColor?: string;
  intensity?: number;
  idleIntensity?: number;
  autoAnimate?: boolean;
  disabled?: boolean;
  className?: string;
  [key: string]: unknown;
}

export default function SpecularButton(props: SpecularButtonProps): ReactElement;
