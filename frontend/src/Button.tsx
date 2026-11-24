import SpecularButton, { type SpecularButtonProps } from "./SpecularButton";

// The one button for the whole project. Colours follow the landing-page headings (--ink, #191F30).
// tone="light" is for dark surfaces (tour card, closing call to action).
export type ButtonProps = SpecularButtonProps & { primary?: boolean; tone?: "ink" | "light" };

export default function Button({ primary, tone = "ink", size = "md", ...rest }: ButtonProps) {
  const ink = tone === "ink";
  const color = ink ? "#191F30" : "#ffffff";
  return (
    <SpecularButton
      size={size}
      radius={10}
      tint={color}
      tintOpacity={primary ? 0.92 : 0.04}
      textColor={primary ? (ink ? "#ffffff" : "#191F30") : color}
      lineColor={primary ? (ink ? "#3447C7" : "#ffffff") : color}
      baseColor={ink ? "#8b93a8" : "#ffffff"}
      {...rest}
    />
  );
}
