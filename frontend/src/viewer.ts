// 3D viewer on That Open Engine 3.6: IFC is converted to fragments in the browser (web-ifc wasm and the
// fragments worker are served locally), then elements are coloured by verdict through the fragments API.
// Only what the IFC contains is drawn: rooms, doors, stairs and any other modelled element.
import * as OBC from "@thatopen/components";
import * as FRAGS from "@thatopen/fragments";
import workerUrl from "@thatopen/fragments/worker?url";
import * as THREE from "three";
import { FRONT_DIRECTION, ISO_DIRECTION, PLAN_DIRECTION, frameBox, implausiblySized, type Vec3 } from "./framing";
import type { Paint } from "./results";
import { Stage, defaultQuality, type Atmosphere, type Quality } from "./stage";

type PaintKey = Paint | "selected";

// Verdict colours: colour-blind-safe hues that never stand alone (the UI pairs them with an icon and a label).
export const VERDICT_COLOR: Record<PaintKey, string> = {
  failed: "#c4321f",
  unchecked: "#d99a1e",
  passed: "#8f969e",
  out_of_scope: "#c9c4b8",
  selected: "#2457d6",
};
const SOLID_OPACITY: Record<PaintKey, number> = { failed: 1, unchecked: 1, passed: 1, out_of_scope: 0.35, selected: 1 };
// Rooms are volumes that would hide everything inside them, so they are drawn as translucent tinted volumes.
const ROOM_OPACITY: Record<PaintKey, number> = { failed: 0.42, unchecked: 0.4, passed: 0.2, out_of_scope: 0.1, selected: 0.5 };
const DIMMED = 0.08;
const UNPAINTED = "#d8d2c4";

/** Geometry larger than this (metres) is almost certainly stored in the wrong unit. */
export const IMPLAUSIBLE_SIZE_M = 200;

export type ViewPreset = "iso" | "plan" | "front";
const PRESET_DIRECTION: Record<ViewPreset, Vec3> = { iso: ISO_DIRECTION, plan: PLAN_DIRECTION, front: FRONT_DIRECTION };

const prefersReducedMotion = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;

function material(paint: PaintKey, room: boolean, dimmed = false): FRAGS.MaterialDefinition {
  const opacity = dimmed ? Math.min(DIMMED, (room ? ROOM_OPACITY : SOLID_OPACITY)[paint]) : (room ? ROOM_OPACITY : SOLID_OPACITY)[paint];
  return {
    color: new THREE.Color(VERDICT_COLOR[paint]),
    renderedFaces: FRAGS.RenderedFaces.TWO,
    opacity,
    transparent: opacity < 1,
  };
}

export interface LoadInfo {
  /** Painted elements whose geometry is implausibly large (likely stored in the wrong unit). */
  implausible: number;
}

export class Viewer {
  private readonly components = new OBC.Components();
  private readonly world: OBC.SimpleWorld<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>;
  private readonly fragments: OBC.FragmentsManager;
  private readonly edges = new THREE.Group();
  private readonly stage: Stage;
  private autoOrbit = false;
  private clock = new THREE.Clock();
  private frameCount = 0;
  private model: FRAGS.FragmentsModel | null = null;
  private paints = new Map<number, Paint>();
  private rooms = new Set<number>();
  private selected: number | null = null;
  private onlyIssues = false;

  constructor(container: HTMLElement) {
    const worlds = this.components.get(OBC.Worlds);
    this.world = worlds.create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>();
    this.world.scene = new OBC.SimpleScene(this.components);
    this.world.scene.setup();
    this.world.renderer = new OBC.SimpleRenderer(this.components, container);
    this.world.renderer.showLogo = false; // That Open is credited in the stage caption and docs/frontend.md
    this.world.camera = new OBC.OrthoPerspectiveCamera(this.components);
    this.components.init();
    this.edges.name = "verdict-outlines";
    this.world.scene.three.add(this.edges);
    this.stage = new Stage(this.world.scene.three, this.world.renderer.three);
    this.stage.setQuality(defaultQuality(navigator as Navigator & { deviceMemory?: number }, window.innerWidth));
    this.world.renderer.onBeforeUpdate.add(() => this.tick());

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
    const box = await this.wholeModelBox(model);
    if (!box.isEmpty()) this.stage.fit(box);
    // an eased fly-in: start further out along the same line of sight, then settle on the framed view
    await this.frame(undefined, false);
    if (!prefersReducedMotion()) {
      const pos = new THREE.Vector3();
      const tgt = new THREE.Vector3();
      this.world.camera.controls.getPosition(pos);
      this.world.camera.controls.getTarget(tgt);
      const far = pos.clone().sub(tgt).multiplyScalar(1.8).add(tgt);
      await this.world.camera.controls.setLookAt(far.x, far.y + pos.distanceTo(tgt) * 0.3, far.z, tgt.x, tgt.y, tgt.z, false);
      void this.world.camera.controls.setLookAt(pos.x, pos.y, pos.z, tgt.x, tgt.y, tgt.z, true);
    }
  }

  setAtmosphere(a: Atmosphere) { this.stage.setAtmosphere(a); }
  setQuality(q: Quality) { this.stage.setQuality(q); }
  get quality(): Quality { return this.stage.quality; }
  setAutoOrbit(on: boolean) { this.autoOrbit = on && !prefersReducedMotion(); }

  /** Per frame: slow auto-orbit, the failed-outline pulse, and shadows on the model's meshes. */
  private tick() {
    const dt = Math.min(0.1, this.clock.getDelta());
    if (this.autoOrbit) void this.world.camera.controls.rotate(dt * 0.12, 0, false);
    const t = this.clock.elapsedTime;
    const pulse = prefersReducedMotion() ? 1 : 0.6 + 0.4 * Math.sin(t * 2.4);
    for (const child of this.edges.children) {
      if (child.userData.pulse) ((child as THREE.LineSegments).material as THREE.LineBasicMaterial).opacity = pulse;
    }
    if (this.model && this.stage.quality === "high" && this.frameCount++ % 30 === 0) {
      this.model.object.traverse((o) => {
        if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; }
      });
    }
  }

  /** Call back with the element under the pointer (throttled) for a hover tooltip; null when over nothing. */
  onHover(callback: (localId: number | null, x: number, y: number) => void): () => void {
    const dom = this.world.renderer!.three.domElement;
    let last = 0;
    let pending = false;
    const onMove = async (e: PointerEvent) => {
      const now = performance.now();
      if (pending || now - last < 90 || e.buttons) return;
      last = now;
      pending = true;
      const hit = await this.fragments.raycast({ camera: this.world.camera.three, mouse: new THREE.Vector2(e.clientX, e.clientY), dom });
      pending = false;
      callback(hit ? hit.localId : null, e.clientX, e.clientY);
    };
    const onLeave = () => callback(null, 0, 0);
    dom.addEventListener("pointermove", onMove);
    dom.addEventListener("pointerleave", onLeave);
    return () => {
      dom.removeEventListener("pointermove", onMove);
      dom.removeEventListener("pointerleave", onLeave);
    };
  }

  /** Local ids of the given GlobalIds in the loaded model (null where not found). */
  async localIdsByGuid(guids: string[]): Promise<(number | null)[]> {
    return this.model ? this.model.getLocalIdsByGuids(guids) : guids.map(() => null);
  }

  async guidsByLocalId(localIds: number[]): Promise<(string | null)[]> {
    return this.model ? this.model.getGuidsByLocalIds(localIds) : localIds.map(() => null);
  }

  /** Colour elements by verdict; `rooms` are drawn as translucent volumes with edge lines. */
  async paint(paints: Map<number, Paint>, rooms = new Set<number>()): Promise<LoadInfo> {
    this.paints = paints;
    this.rooms = rooms;
    await this.buildOutlines();
    await this.repaint();
    const ids = [...paints.keys()];
    const boxes = this.model && ids.length ? await this.model.getBoxes(ids) : [];
    const sizes = new Map<number, Vec3>();
    boxes.forEach((b, i) => {
      if (!b.isEmpty()) sizes.set(ids[i]!, [b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z]);
    });
    return { implausible: implausiblySized(sizes, IMPLAUSIBLE_SIZE_M).length };
  }

  async setOnlyIssues(on: boolean): Promise<void> {
    this.onlyIssues = on;
    const model = this.model;
    if (!model) return;
    if (on) {
      await model.setVisible(undefined, false);
      await model.setVisible(this.issueIds(), true);
    } else {
      await model.resetVisible();
    }
    this.syncEdgeVisibility();
    await this.fragments.core.update(true);
  }

  /** Select an element: it keeps its verdict colour outlined in blue, the rest is dimmed, the camera flies to it. */
  async select(localId: number | null, frame = true): Promise<void> {
    this.selected = localId;
    await this.repaint();
    if (frame && localId !== null) await this.frame([localId]);
  }

  /** Frame the given items, or the whole model, from the current direction (or a preset). */
  async frame(localIds?: number[], animate = true, preset?: ViewPreset): Promise<void> {
    const model = this.model;
    if (!model) return;
    const box = localIds?.length ? await model.getMergedBox(localIds) : await this.wholeModelBox(model);
    if (box.isEmpty()) return;
    const camera = this.world.camera.three as THREE.PerspectiveCamera;
    const controls = this.world.camera.controls;
    const current = new THREE.Vector3();
    const target = new THREE.Vector3();
    controls.getPosition(current);
    controls.getTarget(target);
    const keep = current.sub(target);
    const direction: Vec3 = preset ? PRESET_DIRECTION[preset]
      : localIds?.length && keep.lengthSq() > 0 ? [keep.x, keep.y, keep.z] : ISO_DIRECTION;
    const rect = this.world.renderer!.three.domElement.getBoundingClientRect();
    const f = frameBox({ min: [box.min.x, box.min.y, box.min.z], max: [box.max.x, box.max.y, box.max.z] },
      { fovDeg: camera.fov ?? 60, aspect: rect.width && rect.height ? rect.width / rect.height : 1.4, direction,
        padding: localIds?.length ? 1.6 : 1.08 });
    if (!localIds?.length) {
      // depth range and zoom limits follow the model's size (That Open's defaults stop at 300 m and 1 km)
      camera.near = f.near;
      camera.far = f.far;
      camera.updateProjectionMatrix();
      controls.minDistance = f.minDistance;
      controls.maxDistance = f.maxDistance;
    }
    await controls.setLookAt(...f.position, ...f.target, animate && !prefersReducedMotion());
    await this.fragments.core.update(true);
  }

  async preset(name: ViewPreset): Promise<void> {
    await this.frame(undefined, true, name);
  }

  /** The model's bounds. Tiles stream in, so an empty box is retried a few times before giving up. */
  private async wholeModelBox(model: FRAGS.FragmentsModel): Promise<THREE.Box3> {
    for (let attempt = 0; attempt < 15; attempt++) {
      const box = model.box.isEmpty() ? new THREE.Box3().setFromObject(model.object) : model.box;
      if (!box.isEmpty()) return box;
      await this.fragments.core.update(true);
      await new Promise((resolve) => setTimeout(resolve, 200));
    }
    return new THREE.Box3();
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

  /** Diagnostics for tests: camera, target and model bounds in world units (metres). */
  debugState() {
    const cam = this.world.camera.three as THREE.PerspectiveCamera;
    const target = new THREE.Vector3();
    this.world.camera.controls.getTarget(target);
    const box = this.model ? (this.model.box.isEmpty() ? new THREE.Box3().setFromObject(this.model.object) : this.model.box) : null;
    const v = (p: THREE.Vector3) => [p.x, p.y, p.z].map((n) => Math.round(n * 100) / 100);
    let allCornersInView: boolean | null = null;
    if (box && !box.isEmpty()) {
      cam.updateMatrixWorld();
      allCornersInView = [0, 1, 2, 3, 4, 5, 6, 7].every((i) => {
        const p = new THREE.Vector3(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z)
          .project(cam);
        return Math.abs(p.x) <= 1.001 && Math.abs(p.y) <= 1.001 && p.z > -1 && p.z < 1;
      });
    }
    return {
      camera: v(cam.position), target: v(target), near: cam.near, far: cam.far, fov: cam.fov,
      maxDistance: this.world.camera.controls.maxDistance,
      box: box && !box.isEmpty() ? { min: v(box.min), max: v(box.max) } : null,
      cameraOutsideModel: box ? !box.containsPoint(cam.position) : null,
      allCornersInView,
      edges: this.edges.children.length,
      memory: { ...this.world.renderer!.three.info.memory },
      quality: this.stage.quality,
      atmosphere: this.stage.atmosphere,
    };
  }

  /** Diagnostics for tests: edge sets that do not lie inside their own room's box (should be 0). */
  async debugMisplacedEdges(): Promise<number> {
    const model = this.model;
    if (!model) return 0;
    let misplaced = 0;
    for (const child of this.edges.children) {
      const [box] = await model.getBoxes([child.userData.localId as number]);
      const edgeBox = new THREE.Box3().setFromObject(child);
      if (!box || box.isEmpty() || !box.clone().expandByScalar(Math.max(0.01, box.getSize(new THREE.Vector3()).length() * 0.01)).containsBox(edgeBox)) misplaced += 1;
    }
    return misplaced;
  }

  async dispose(): Promise<void> {
    await this.clearModel();
    this.stage.dispose();
    this.components.dispose();
  }

  private issueIds(): number[] {
    return [...this.paints].filter(([, p]) => p === "failed" || p === "unchecked").map(([id]) => id);
  }

  private async repaint(): Promise<void> {
    const model = this.model;
    if (!model) return;
    await model.resetHighlight();
    const dim = this.selected !== null;
    if (dim) {
      // everything that is not audited (slabs, walls...) fades too, so the selection stands out
      const all = await model.getItemsIdsWithGeometry();
      const others = all.filter((id) => !this.paints.has(id) && id !== this.selected);
      if (others.length) await model.highlight(others, { color: new THREE.Color(UNPAINTED), renderedFaces: FRAGS.RenderedFaces.TWO, opacity: DIMMED, transparent: true });
    }
    const groups = new Map<string, { paint: Paint; room: boolean; ids: number[] }>();
    for (const [id, paint] of this.paints) {
      if (id === this.selected) continue;
      const room = this.rooms.has(id);
      const key = `${paint}/${room}`;
      const group = groups.get(key) ?? { paint, room, ids: [] };
      group.ids.push(id);
      groups.set(key, group);
    }
    for (const { paint, room, ids } of groups.values()) await model.highlight(ids, material(paint, room, dim));
    if (this.selected !== null) await model.highlight([this.selected], material("selected", this.rooms.has(this.selected)));
    this.styleEdges();
    if (this.onlyIssues) await this.setOnlyIssues(true);
    await this.fragments.core.update(true);
  }

  /** Verdict outlines for every audited element, built from its real mesh (nothing that is not in the model). */
  private async buildOutlines(): Promise<void> {
    this.disposeEdges();
    const model = this.model;
    if (!model || this.paints.size === 0) return;
    const ids = [...this.paints.keys()];
    const geometries = await model.getItemsGeometry(ids);
    geometries.forEach((meshes, i) => {
      for (const mesh of meshes) {
        if (!mesh.positions || !mesh.indices) continue;
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.BufferAttribute(Float32Array.from(mesh.positions), 3));
        geometry.setIndex(new THREE.BufferAttribute(mesh.indices, 1));
        const edges = new THREE.EdgesGeometry(geometry, 25);
        geometry.dispose();
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: VERDICT_COLOR.passed, transparent: true }));
        line.applyMatrix4(mesh.transform);
        // rooms without geometry return no meshes, so the array index is not the room: use the mesh's own id
        line.userData.localId = mesh.localId ?? ids[i];
        line.renderOrder = 2;
        this.edges.add(line);
      }
    });
    // fragments meshes live under the model's object; follow its transform (web-ifc may move it to the origin)
    this.edges.matrixAutoUpdate = false;
    this.edges.matrix.copy(model.object.matrixWorld);
  }

  private styleEdges(): void {
    for (const child of this.edges.children) {
      const line = child as THREE.LineSegments<THREE.EdgesGeometry, THREE.LineBasicMaterial>;
      const id = line.userData.localId as number;
      const paint: PaintKey = id === this.selected ? "selected" : this.paints.get(id) ?? "passed";
      line.material.color.set(VERDICT_COLOR[paint]).multiplyScalar(paint === "selected" ? 1 : 0.8); // a shade darker than the fill
      line.material.opacity = this.selected !== null && id !== this.selected ? 0.15 : paint === "out_of_scope" ? 0.4 : 0.95;
      line.userData.pulse = paint === "failed" && (this.selected === null);
    }
    this.syncEdgeVisibility();
  }

  private syncEdgeVisibility(): void {
    const issues = new Set(this.issueIds());
    for (const child of this.edges.children) child.visible = !this.onlyIssues || issues.has(child.userData.localId as number);
  }

  private disposeEdges(): void {
    for (const child of [...this.edges.children]) {
      const line = child as THREE.LineSegments<THREE.EdgesGeometry, THREE.LineBasicMaterial>;
      line.geometry.dispose();
      line.material.dispose();
      this.edges.remove(line);
    }
  }

  async clearModel(): Promise<void> {
    this.disposeEdges();
    for (const [id] of this.fragments.list) await this.fragments.core.disposeModel(id);
    this.model = null;
    this.paints.clear();
    this.rooms.clear();
    this.selected = null;
  }
}
