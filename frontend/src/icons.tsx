// Authored SVG icons, one stroke weight. Status icons use distinct shapes so status never depends on colour.
import type { SVGProps } from "react";
import type { Status, Verdict } from "./api";

type IconProps = SVGProps<SVGSVGElement>;

function Svg({ children, ...props }: IconProps) {
  return (
    <svg viewBox="0 0 20 20" width="1.1em" height="1.1em" fill="none" stroke="currentColor" strokeWidth="1.75"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false" {...props}>
      {children}
    </svg>
  );
}

export const IconFailed = (p: IconProps) => (
  <Svg {...p}><circle cx="10" cy="10" r="7.5" /><path d="M7.2 7.2l5.6 5.6M12.8 7.2l-5.6 5.6" /></Svg>
);
export const IconUnchecked = (p: IconProps) => (
  <Svg {...p}><path d="M10 2.8l7.6 13.4H2.4z" /><path d="M10 8v3.6M10 14.1v.1" /></Svg>
);
export const IconPassed = (p: IconProps) => (
  <Svg {...p}><circle cx="10" cy="10" r="7.5" /><path d="M6.6 10.2l2.3 2.3 4.6-4.8" /></Svg>
);
export const IconOutOfScope = (p: IconProps) => (
  <Svg {...p}><circle cx="10" cy="10" r="7.5" strokeDasharray="2.4 2.2" /><path d="M6.8 10h6.4" /></Svg>
);
export const IconUpload = (p: IconProps) => (
  <Svg {...p}><path d="M10 13V3.5M6.2 7.2L10 3.4l3.8 3.8M3.5 13.5v3h13v-3" /></Svg>
);
export const IconDownload = (p: IconProps) => (
  <Svg {...p}><path d="M10 3.5V13M6.2 9.3L10 13.1l3.8-3.8M3.5 13.5v3h13v-3" /></Svg>
);
export const IconExternal = (p: IconProps) => (
  <Svg {...p}><path d="M11.5 3.5h5v5M16.3 3.7L9.5 10.5M14.5 11.5v5h-11v-11h5" /></Svg>
);
export const IconReset = (p: IconProps) => (
  <Svg {...p}><path d="M3.8 9.5a6.3 6.3 0 1 0 1.9-4.6M3.6 3.3v3.4H7" /></Svg>
);

export const VERDICT_ICON: Record<Verdict, (p: IconProps) => React.JSX.Element> = {
  failed: IconFailed,
  unchecked: IconUnchecked,
  passed: IconPassed,
  out_of_scope: IconOutOfScope,
};

export const STATUS_ICON: Record<Status, (p: IconProps) => React.JSX.Element> = {
  noncompliant: IconFailed,
  incomplete: IconUnchecked,
  compliant: IconPassed,
  nothing_checked: IconOutOfScope,
};
