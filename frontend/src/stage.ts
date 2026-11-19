// The environment around the model: sky, sun, ground and fog. Nothing here comes from the IFC and nothing here
// pretends to: it is the light table the model sits on. Built once per viewer and resized to each model.
import * as THREE from "three";

export type Atmosphere = "golden" | "neutral";
export type Quality = "low" | "high";

const SKY: Record<Atmosphere, { top: string; horizon: string; ground: string; fog: string; sun: string; sunI: number; hemiSky: string; hemiGround: string; hemiI: number }> = {
  // a restrained golden hour: desaturated, so verdict colours stay the strongest hues on screen
  golden: { top: "#8d9fb4", horizon: "#e6dcc9", ground: "#cfc6b4", fog: "#e2d8c4", sun: "#ffe2bd", sunI: 2.4, hemiSky: "#e3e8ef", hemiGround: "#b9ac95", hemiI: 1.05 },
  neutral: { top: "#15181d", horizon: "#2a2e36", ground: "#23262c", fog: "#22252b", sun: "#f3efe6", sunI: 2.0, hemiSky: "#c9ccd2", hemiGround: "#3a3d44", hemiI: 1.2 },
};

const VERT = `varying vec3 vWorld; void main(){ vec4 w = modelMatrix * vec4(position,1.0); vWorld = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
const FRAG = `uniform vec3 top; uniform vec3 horizon; uniform vec3 bottom; uniform vec3 centre; varying vec3 vWorld;
void main(){ float h = normalize(vWorld - centre).y; vec3 c = h > 0.0 ? mix(horizon, top, pow(h, 0.55)) : mix(horizon, bottom, pow(-h, 0.4));
gl_FragColor = vec4(c, 1.0);
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`;

export class Stage {
  readonly group = new THREE.Group();
  private readonly sky: THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
  private readonly sun = new THREE.DirectionalLight();
  private readonly hemi = new THREE.HemisphereLight();
  private readonly ground: THREE.Mesh<THREE.PlaneGeometry, THREE.ShadowMaterial>;
  private readonly paving: THREE.Mesh<THREE.PlaneGeometry, THREE.MeshStandardMaterial>;
  private grid: THREE.GridHelper | null = null;
  atmosphere: Atmosphere = "golden";
  quality: Quality = "low";

  constructor(private readonly scene: THREE.Scene, private readonly renderer: THREE.WebGLRenderer) {
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), new THREE.ShaderMaterial({
      vertexShader: VERT, fragmentShader: FRAG, side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: { top: { value: new THREE.Color() }, horizon: { value: new THREE.Color() }, bottom: { value: new THREE.Color() }, centre: { value: new THREE.Vector3() } },
    }));
    this.sky.name = "sky";
    this.sky.renderOrder = -10;
    this.ground = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShadowMaterial({ opacity: 0.22 }));
    this.ground.rotation.x = -Math.PI / 2;
    this.ground.receiveShadow = true;
    this.paving = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshStandardMaterial({ roughness: 0.95, metalness: 0 }));
    this.paving.rotation.x = -Math.PI / 2;
    this.paving.position.y = -0.002;
    this.sun.castShadow = true;
    this.group.add(this.sky, this.paving, this.ground, this.sun, this.sun.target, this.hemi);
    this.group.name = "environment";
    scene.add(this.group);
    this.setAtmosphere("golden");
    this.fit(new THREE.Box3(new THREE.Vector3(-5, 0, -5), new THREE.Vector3(5, 3, 5)));
  }

  setAtmosphere(a: Atmosphere) {
    this.atmosphere = a;
    const s = SKY[a];
    const u = this.sky.material.uniforms;
    (u.top!.value as THREE.Color).set(s.top);
    (u.horizon!.value as THREE.Color).set(s.horizon);
    (u.bottom!.value as THREE.Color).set(s.ground);
    this.paving.material.color.set(s.ground);
    this.sun.color.set(s.sun);
    this.sun.intensity = s.sunI;
    this.hemi.color.set(s.hemiSky);
    this.hemi.groundColor.set(s.hemiGround);
    this.hemi.intensity = s.hemiI;
    this.ground.material.opacity = a === "golden" ? 0.22 : 0.35;
    if (this.scene.fog) (this.scene.fog as THREE.Fog).color.set(s.fog);
    if (this.grid) (this.grid.material as THREE.LineBasicMaterial).color.set(a === "golden" ? "#b3a88f" : "#3b3f47");
  }

  setQuality(q: Quality) {
    this.quality = q;
    this.renderer.setPixelRatio(q === "high" ? Math.min(window.devicePixelRatio || 1, 2) : 1);
    this.renderer.shadowMap.enabled = q === "high";
    this.sun.castShadow = q === "high";
    this.sun.shadow.mapSize.set(q === "high" ? 2048 : 512, q === "high" ? 2048 : 512);
    this.sun.shadow.map?.dispose();
    this.sun.shadow.map = null;
  }

  /** Size sky, ground, grid, fog and the sun's shadow camera to the model's box (metres). */
  fit(box: THREE.Box3) {
    const size = box.getSize(new THREE.Vector3());
    const centre = box.getCenter(new THREE.Vector3());
    const r = Math.max(2, size.length() / 2);
    const floor = box.min.y - 0.01;
    this.sky.scale.setScalar(r * 30);
    this.sky.position.copy(centre);
    (this.sky.material.uniforms.centre!.value as THREE.Vector3).copy(centre);
    for (const m of [this.ground, this.paving]) {
      m.scale.set(r * 40, r * 40, 1);
      m.position.set(centre.x, m === this.paving ? floor - 0.002 : floor, centre.z);
    }
    if (this.grid) {
      this.grid.geometry.dispose();
      (this.grid.material as THREE.Material).dispose();
      this.group.remove(this.grid);
    }
    const step = 10 ** Math.floor(Math.log10(Math.max(0.5, r / 4)));
    const span = Math.ceil((r * 8) / step) * step;
    this.grid = new THREE.GridHelper(span, Math.round(span / step), "#b3a88f", "#b3a88f");
    const gm = this.grid.material as THREE.LineBasicMaterial;
    gm.transparent = true;
    gm.opacity = 0.35;
    gm.depthWrite = false;
    this.grid.position.set(centre.x, floor + 0.001, centre.z);
    this.group.add(this.grid);
    this.scene.fog = new THREE.Fog(SKY[this.atmosphere].fog, r * 2.5, r * 9);
    this.setAtmosphere(this.atmosphere);
    // a low sun from the south-west, so faces read in light and shade
    this.sun.position.set(centre.x - r * 1.6, centre.y + r * 1.5, centre.z + r * 1.1);
    this.sun.target.position.copy(centre);
    const cam = this.sun.shadow.camera;
    cam.left = cam.bottom = -r * 1.4;
    cam.right = cam.top = r * 1.4;
    cam.near = r * 0.1;
    cam.far = r * 6;
    cam.updateProjectionMatrix();
  }

  dispose() {
    this.scene.remove(this.group);
    this.sky.geometry.dispose();
    this.sky.material.dispose();
    this.ground.geometry.dispose();
    this.ground.material.dispose();
    this.paving.geometry.dispose();
    this.paving.material.dispose();
    this.grid?.geometry.dispose();
    (this.grid?.material as THREE.Material | undefined)?.dispose();
    this.sun.shadow.map?.dispose();
  }
}

/** Low quality on constrained devices (few cores, little memory, or small screens); High otherwise. */
export function defaultQuality(nav: { hardwareConcurrency?: number; deviceMemory?: number }, width: number): Quality {
  if ((nav.hardwareConcurrency ?? 8) <= 4) return "low";
  if ((nav.deviceMemory ?? 8) <= 4) return "low";
  if (width < 900) return "low";
  return "high";
}
