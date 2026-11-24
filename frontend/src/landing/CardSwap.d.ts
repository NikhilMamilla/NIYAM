import type { CSSProperties, ForwardRefExoticComponent, HTMLAttributes, ReactNode, RefAttributes } from "react";

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
  children?: ReactNode;
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
  speed?: number;
  bounce?: number;
  parallax?: number;
  hoverSpread?: number;
  dim?: number;
  cardRadius?: number;
  intro?: boolean;
  theme?: "dark" | "light";
  onCardClick?: (index: number) => void;
  onChange?: (index: number) => void;
  className?: string;
  style?: CSSProperties;
}

declare const CardSwap: ForwardRefExoticComponent<CardSwapProps & RefAttributes<CardSwapHandle>>;
export default CardSwap;
export declare const Card: ForwardRefExoticComponent<HTMLAttributes<HTMLDivElement> & { customClass?: string } & RefAttributes<HTMLDivElement>>;
