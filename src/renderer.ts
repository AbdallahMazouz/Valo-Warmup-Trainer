// =====================================================================
// renderer.ts — Three.js scene, lighting, arena geometry
// =====================================================================

import * as THREE from 'three';
import {
  COL_TARGET_IDLE, COL_TARGET_HIT,
  COL_ARENA_FLOOR, COL_ARENA_WALL, COL_ARENA_CEIL,
  COL_AMBIENT, COL_FOG,
  TARGET_HIT_FLASH_MS,
  NEAR_PLANE, FAR_PLANE,
} from './constants';

export class Renderer {
  scene:    THREE.Scene;
  camera:   THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;

  private targetMeshes = new Map<string, THREE.Mesh>();
  private hitTimers    = new Map<string, number>();
  private matIdle:  THREE.MeshPhongMaterial;
  private matHit:   THREE.MeshPhongMaterial;

  constructor(canvas: HTMLCanvasElement, fov: number) {
    // Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(COL_FOG);
    this.scene.fog = new THREE.Fog(COL_FOG, 30, FAR_PLANE);

    // Camera
    this.camera = new THREE.PerspectiveCamera(
      fov, canvas.width / canvas.height, NEAR_PLANE, FAR_PLANE,
    );

    // WebGL renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      powerPreference: 'high-performance',
    });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // Materials
    this.matIdle = new THREE.MeshPhongMaterial({
      color: COL_TARGET_IDLE,
      emissive: COL_TARGET_IDLE,
      emissiveIntensity: 0.35,
      shininess: 60,
    });
    this.matHit = new THREE.MeshPhongMaterial({
      color: COL_TARGET_HIT,
      emissive: COL_TARGET_HIT,
      emissiveIntensity: 0.9,
    });

    this.buildArena();
    this.buildLighting();
  }

  // ── Arena ──────────────────────────────────────────────────────────
  private buildArena(): void {
    const W = 40, H = 8, D = 40;
    const floorGeo  = new THREE.PlaneGeometry(W, D, 20, 20);
    const wallGeo   = new THREE.PlaneGeometry(W, H);
    const ceilGeo   = new THREE.PlaneGeometry(W, D);

    const matFloor = new THREE.MeshPhongMaterial({ color: COL_ARENA_FLOOR, shininess: 20 });
    const matWall  = new THREE.MeshPhongMaterial({ color: COL_ARENA_WALL, side: THREE.DoubleSide });
    const matCeil  = new THREE.MeshPhongMaterial({ color: COL_ARENA_CEIL });

    // Floor
    const floor = new THREE.Mesh(floorGeo, matFloor);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Ceiling
    const ceil = new THREE.Mesh(ceilGeo, matCeil);
    ceil.rotation.x = Math.PI / 2;
    ceil.position.y = H;
    this.scene.add(ceil);

    // Walls
    const wallPositions: [number, number, number, number][] = [
      [0,  H/2, -D/2, 0],
      [0,  H/2,  D/2, Math.PI],
      [-W/2, H/2, 0,  Math.PI/2],
      [ W/2, H/2, 0, -Math.PI/2],
    ];
    for (const [x, y, z, ry] of wallPositions) {
      const m = new THREE.Mesh(wallGeo, matWall);
      m.position.set(x, y, z);
      m.rotation.y = ry;
      this.scene.add(m);
    }

    // Grid helper (subtle)
    const grid = new THREE.GridHelper(W, 20, 0x2a2a45, 0x2a2a45);
    (grid.material as THREE.Material).opacity = 0.3;
    (grid.material as THREE.Material).transparent = true;
    this.scene.add(grid);

    // Cover boxes (for tactical scenarios)
    this.addCoverBox(-8, 0, -8,  2, 2, 0.4, 0x1e1e30);
    this.addCoverBox( 8, 0, -8,  2, 2, 0.4, 0x1e1e30);
    this.addCoverBox(-6, 0, -14, 0.4, 2, 3,  0x181828);
    this.addCoverBox( 6, 0, -14, 0.4, 2, 3,  0x181828);
  }

  private addCoverBox(
    x: number, y: number, z: number,
    w: number, h: number, d: number,
    color: number,
  ): void {
    const geo = new THREE.BoxGeometry(w, h, d);
    const mat = new THREE.MeshPhongMaterial({ color });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(x, y + h / 2, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    this.scene.add(mesh);
  }

  // ── Lighting ────────────────────────────────────────────────────────
  private buildLighting(): void {
    const ambient = new THREE.AmbientLight(COL_AMBIENT, 0.7);
    this.scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
    dirLight.position.set(8, 14, 6);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.set(1024, 1024);
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far  = 60;
    dirLight.shadow.camera.left = dirLight.shadow.camera.bottom = -20;
    dirLight.shadow.camera.right = dirLight.shadow.camera.top  =  20;
    this.scene.add(dirLight);

    // Accent fill from below
    const fillLight = new THREE.PointLight(0x2a2060, 0.4, 30);
    fillLight.position.set(0, -1, 0);
    this.scene.add(fillLight);
  }

  // ── Target management ────────────────────────────────────────────────
  addTarget(id: string, position: THREE.Vector3, radius: number): void {
    const geo  = new THREE.SphereGeometry(radius, 20, 14);
    const mesh = new THREE.Mesh(geo, this.matIdle.clone());
    mesh.position.copy(position);
    mesh.castShadow = true;
    this.scene.add(mesh);
    this.targetMeshes.set(id, mesh);
  }

  updateTargetPosition(id: string, position: THREE.Vector3): void {
    this.targetMeshes.get(id)?.position.copy(position);
  }

  flashTarget(id: string): void {
    const mesh = this.targetMeshes.get(id);
    if (!mesh) return;
    (mesh.material as THREE.MeshPhongMaterial).copy(this.matHit);
    this.hitTimers.set(id, performance.now() + TARGET_HIT_FLASH_MS);
  }

  removeTarget(id: string): void {
    const mesh = this.targetMeshes.get(id);
    if (mesh) {
      this.scene.remove(mesh);
      mesh.geometry.dispose();
      (mesh.material as THREE.Material).dispose();
      this.targetMeshes.delete(id);
      this.hitTimers.delete(id);
    }
  }

  clearTargets(): void {
    for (const id of [...this.targetMeshes.keys()]) this.removeTarget(id);
  }

  // ── Resize ──────────────────────────────────────────────────────────
  resize(w: number, h: number): void {
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  }

  updateFov(fov: number): void {
    this.camera.fov = fov;
    this.camera.updateProjectionMatrix();
  }

  // ── Render loop ─────────────────────────────────────────────────────
  render(): void {
    const now = performance.now();

    // Restore hit material after flash timer
    for (const [id, expiry] of this.hitTimers) {
      if (now >= expiry) {
        const mesh = this.targetMeshes.get(id);
        if (mesh) (mesh.material as THREE.MeshPhongMaterial).copy(this.matIdle);
        this.hitTimers.delete(id);
      }
    }

    // Subtle target pulse
    for (const mesh of this.targetMeshes.values()) {
      const mat = mesh.material as THREE.MeshPhongMaterial;
      if (!this.hitTimers.has(
        [...this.targetMeshes.entries()].find(([, m]) => m === mesh)?.[0] ?? '',
      )) {
        mat.emissiveIntensity = 0.25 + 0.15 * Math.sin(now * 0.004);
      }
    }

    this.renderer.render(this.scene, this.camera);
  }

  getTargetPosition(id: string): THREE.Vector3 | undefined {
    return this.targetMeshes.get(id)?.position.clone();
  }
}
