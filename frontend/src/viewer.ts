// 3D viewer on That Open Engine 3.6: IFC is converted to fragments in the browser (web-ifc wasm and the
// fragments worker are served locally), then elements are coloured by verdict through the fragments API.
import * as OBC from "@thatopen/components";
import * as FRAGS from "@thatopen/fragments";
import workerUrl from "@thatopen/fragments/worker?url";
import * as THREE from "three";
import type { Paint } from "./results";

const COLORS: Record<Paint | "selected", string> = {
  failed: "#c81e1e",
  unchecked: "#f0a202",
  passed: "#a3a7ad",
  out_of_scope: "#c9ccd1",
  selected: "#1d4ed8",
};
const OPACITY: Record<Paint | "selected", number> = {
  failed: 1, unchecked: 1, passed: 1, out_of_scope: 0.25, selected: 1,
};

const material = (paint: Paint | "selected"): FRAGS.MaterialDefinition => ({
  color: new THREE.Color(COLORS[paint]),
  renderedFaces: FRAGS.RenderedFaces.TWO,
  opacity: OPACITY[paint],
  transparent: OPACITY[paint] < 1,
});

const prefersReducedMotion = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

export class Viewer {
  private readonly components = new OBC.Components();
  private readonly world: OBC.SimpleWorld<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>;
  private readonly fragments: OBC.FragmentsManager;
  private model: FRAGS.FragmentsModel | null = null;
  private paints = new Map<number, Paint>();
  private selected: number | null = null;
  private onlyIssues = false;

  constructor(container: HTMLElement) {
    const worlds = this.components.get(OBC.Worlds);
    this.world = worlds.create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>();
    this.world.scene = new OBC.SimpleScene(this.components);
    this.world.scene.setup();
    this.world.scene.three.background = new THREE.Color("#f4f5f7");
    this.world.renderer = new OBC.SimpleRenderer(this.components, container);
    this.world.camera = new OBC.OrthoPerspectiveCamera(this.components);
    this.components.init();

    this.fragments = this.components.get(OBC.FragmentsManager);
    this.fragments.init(workerUrl);
    this.world.camera.controls.addEventListener("rest", () => void this.fragments.core.update(true));
    // attach the camera as soon as a model is registered, before its first render
    this.fragments.list.onItemSet.add(({ value }) => value.useCamera(this.world.camera.three));
  }

  /** Convert the IFC to fragments in the browser and show it framed. */
  async load(bytes: Uint8Array): Promise<void> {
    await this.clearModel();
    const loader = this.components.get(OBC.IfcLoader);
    await loader.setup({ autoSetWasm: false, wasm: { path: "/web-ifc/", absolute: true } });
    const model = await loader.load(bytes, true, "model");
    this.world.scene.three.add(model.object);
    this.model = model;
    await this.fragments.core.update(true);
    // three-quarter view from the front-left and above, so rows of elements do not hide each other
    await this.world.camera.controls.rotateTo(Math.PI * 0.2, Math.PI * 0.36, false);
    await this.frame();
  }

  /** Local ids of the given GlobalIds in the loaded model (null where not found). */
  async localIdsByGuid(guids: string[]): Promise<(number | null)[]> {
    return this.model ? this.model.getLocalIdsByGuids(guids) : guids.map(() => null);
  }

  async guidsByLocalId(localIds: number[]): Promise<(string | null)[]> {
    return this.model ? this.model.getGuidsByLocalIds(localIds) : localIds.map(() => null);
  }

  async paint(paints: Map<number, Paint>): Promise<void> {
    this.paints = paints;
    await this.repaint();
  }

  async setOnlyIssues(on: boolean): Promise<void> {
    this.onlyIssues = on;
    const model = this.model;
    if (!model) return;
    if (on) {
      await model.setVisible(undefined, false);
      const issues = [...this.paints].filter(([, p]) => p === "failed" || p === "unchecked").map(([id]) => id);
      await model.setVisible(issues, true);
    } else {
      await model.resetVisible();
    }
    await this.fragments.core.update(true);
  }

  async select(localId: number | null, frame = true): Promise<void> {
    this.selected = localId;
    await this.repaint();
    if (frame && localId !== null) await this.frame([localId]);
  }

  /** Frame the given items, or the whole model. */
  async frame(localIds?: number[]): Promise<void> {
    const model = this.model;
    if (!model) return;
    const box = localIds?.length ? await model.getMergedBox(localIds) : new THREE.Box3().setFromObject(model.object);
    if (box.isEmpty()) return;
    const padded = box.clone().expandByScalar(localIds?.length ? 1.5 : 0.5);
    await this.world.camera.controls.fitToBox(padded, !prefersReducedMotion());
    await this.fragments.core.update(true);
  }

  /** Call back with the local id under the pointer on click (null for empty space). Drags are ignored. */
  onPick(callback: (localId: number | null) => void): () => void {
    const dom = this.world.renderer!.three.domElement;
    let down: { x: number; y: number } | null = null;
    const onDown = (e: PointerEvent) => (down = { x: e.clientX, y: e.clientY });
    const onUp = async (e: PointerEvent) => {
      if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 4) return;
      const mouse = new THREE.Vector2(e.clientX, e.clientY); // raycast converts client px to NDC itself
      const hit = await this.fragments.raycast({ camera: this.world.camera.three, mouse, dom });
      callback(hit ? hit.localId : null);
    };
    dom.addEventListener("pointerdown", onDown);
    dom.addEventListener("pointerup", onUp);
    return () => {
      dom.removeEventListener("pointerdown", onDown);
      dom.removeEventListener("pointerup", onUp);
    };
  }

  async dispose(): Promise<void> {
    await this.clearModel();
    this.components.dispose();
  }

  private async repaint(): Promise<void> {
    const model = this.model;
    if (!model) return;
    await model.resetHighlight();
    const groups = new Map<Paint, number[]>();
    for (const [id, paint] of this.paints) groups.set(paint, [...(groups.get(paint) ?? []), id]);
    for (const [paint, ids] of groups) await model.highlight(ids, material(paint));
    if (this.selected !== null) await model.highlight([this.selected], material("selected"));
    if (this.onlyIssues) await this.setOnlyIssues(true);
    await this.fragments.core.update(true);
  }

  async clearModel(): Promise<void> {
    for (const [id] of this.fragments.list) await this.fragments.core.disposeModel(id);
    this.model = null;
    this.paints.clear();
    this.selected = null;
  }
}
