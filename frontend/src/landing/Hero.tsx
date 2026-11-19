// The hero figure: an isometric whiteprint schematic of a small building. It is an illustration, not a model and
// not a result; its callouts use words, never numbers.
import { IconFailed, IconPassed, IconUnchecked } from "../icons";

const S = 29;          // drawing scale
const OX = 268, OY = 74;
const C = Math.cos(Math.PI / 6), N = Math.sin(Math.PI / 6);
const iso = (x: number, y: number, z = 0): [number, number] => [OX + (x - y) * C * S, OY + (x + y) * N * S - z * S];
const P = (pts: [number, number, number?][]) => pts.map(([x, y, z], i) => `${i ? "L" : "M"}${iso(x, y, z ?? 0).map((n) => n.toFixed(1)).join(" ")}`).join(" ");

const W = 12, D = 8, H = 3;
// plan partitions: [x1, y1, x2, y2]
const WALLS: [number, number, number, number][] = [[5, 0, 5, 8], [5, 4, 12, 4], [0, 5, 5, 5], [9, 0, 9, 4]];

function Room({ pts, cls }: { pts: [number, number][]; cls: string }) {
  return <path d={`${P(pts.map(([x, y]) => [x, y, 0]))} Z`} className={cls} />;
}

/** A verdict mark drawn on the sheet: the same shapes as the UI icons, so colour is never the only signal. */
function Mark({ at, kind }: { at: [number, number]; kind: "fail" | "warn" | "pass" }) {
  const [x, y] = at;
  return (
    <g className={`mark mark-${kind}`} transform={`translate(${x.toFixed(1)} ${y.toFixed(1)})`}>
      <line x1={0} y1={0} x2={0} y2={-24} className="leader" />
      <g transform="translate(0 -36)">
        {kind === "warn" ? <path d="M0 -11 L11 8 L-11 8 Z" className="mark-shape" /> : <circle r={11} className="mark-shape" />}
        {kind === "fail" && <path d="M-4.5 -4.5 L4.5 4.5 M4.5 -4.5 L-4.5 4.5" className="mark-glyph" />}
        {kind === "warn" && <path d="M0 -3 V2.5 M0 5.5 V5.6" className="mark-glyph" />}
        {kind === "pass" && <path d="M-5 0.5 L-1.5 4 L5 -3" className="mark-glyph" />}
      </g>
      <circle r={3} className="mark-dot" />
    </g>
  );
}

export function HeroDrawing() {
  return (
    <figure className="hero-figure">
      <svg viewBox="0 0 600 440" className="hero-svg" role="img"
           aria-label="Schematic drawing of a small building: a bathroom is marked as failing a rule, an exit door as not checked because data is missing, and a bedroom as passing. An illustration, not a real result.">
        {/* grid bubbles, as on a plan sheet: letters along one side, numbers along the other */}
        {[0, 5, 12].map((gx, i) => {
          const [bx, by] = iso(gx, -1.9);
          return <g key={`a${gx}`} className="bubble"><path d={P([[gx, -1.3, 0], [gx, 0, 0]])} className="print-line thin" /><circle cx={bx} cy={by} r={10} /><text x={bx} y={by + 4} textAnchor="middle">{"ABC"[i]}</text></g>;
        })}
        {[0, 4, 8].map((gy, i) => {
          const [bx, by] = iso(W + 1.9, gy);
          return <g key={`n${gy}`} className="bubble"><path d={P([[W, gy, 0], [W + 1.3, gy, 0]])} className="print-line thin" /><circle cx={bx} cy={by} r={10} /><text x={bx} y={by + 4} textAnchor="middle">{i + 1}</text></g>;
        })}

        <Room pts={[[0, 5], [5, 5], [5, 8], [0, 8]]} cls="room-fail" />
        <Room pts={[[5, 4], [12, 4], [12, 8], [5, 8]]} cls="room-pass" />

        <path d={`${P([[0, 0], [W, 0], [W, D], [0, D]])} Z`} className="print-line" />
        {WALLS.map(([x1, y1, x2, y2], i) => <path key={`w${i}`} d={P([[x1, y1], [x2, y2]])} className="print-line" />)}
        {WALLS.map(([x1, y1, x2, y2], i) => <path key={`t${i}`} d={P([[x1, y1, H], [x2, y2, H]])} className="print-line faint" />)}
        <path d={`${P([[0, 0, H], [W, 0, H], [W, D, H], [0, D, H]])} Z`} className="print-line" />
        {[[0, 0], [W, 0], [W, D], [0, D], [5, 0], [5, 8], [12, 4], [9, 0]].map(([x, y], i) => (
          <path key={`v${i}`} d={P([[x!, y!, 0], [x!, y!, H]])} className={i < 4 ? "print-line" : "print-line faint"} />
        ))}
        {/* stair in the hall, drawn as a plan symbol: treads and the walking line */}
        {[0, 1, 2, 3, 4, 5, 6].map((s) => <path key={`s${s}`} d={P([[1 + s * 0.45, 0.8], [1 + s * 0.45, 3.2]])} className="print-line thin" />)}
        <path d={P([[1, 2], [3.9, 2]])} className="print-line thin" />
        <path d={P([[3.6, 1.75], [3.95, 2], [3.6, 2.25]])} className="print-line thin" />
        {/* doors as swing arcs */}
        <path d={`M${iso(W, 1.2).join(" ")} A ${S * 1.15} ${S * 0.62} 0 0 1 ${iso(10.85, 2.0).join(" ")}`} className="print-line door-unchecked" />
        <path d={`M${iso(5, 6).join(" ")} A ${S} ${S * 0.55} 0 0 0 ${iso(4.1, 6.6).join(" ")}`} className="print-line thin" />

        <Mark at={iso(2.5, 6.5, 0)} kind="fail" />
        <Mark at={iso(11.6, 1.4, 0)} kind="warn" />
        <Mark at={iso(8.5, 6, 0)} kind="pass" />
      </svg>
      <ul className="hero-callouts">
        <li className="callout callout-fail"><IconFailed /><span><strong>Bathroom</strong> smaller than the minimum area: fails</span></li>
        <li className="callout callout-warn"><IconUnchecked /><span><strong>Exit door</strong> width not in the model: could not be checked</span></li>
        <li className="callout callout-pass"><IconPassed /><span><strong>Bedroom</strong> height is enough: passes</span></li>
      </ul>
      <figcaption>Schematic for illustration. Not a building, not a result.</figcaption>
    </figure>
  );
}
