import { useEffect, useImperativeHandle, useRef } from "react";
import * as THREE from "three";

const COLOR_ESCALON = 0xd85a30;
const COLOR_ZANCA = 0x2b2620;
const COLOR_POSTE = 0x888780;

export default function Escalera3D({ tipo, resultado, form, capturaRef }) {
  const contenedorRef = useRef(null);
  const rendererRef = useRef(null);

  useImperativeHandle(capturaRef, () => ({
    capturar: () => rendererRef.current?.domElement.toDataURL("image/png") ?? null,
  }), []);

  useEffect(() => {
    const contenedor = contenedorRef.current;
    if (!contenedor || !resultado || resultado.tipo !== tipo) return;

    const w = contenedor.clientWidth;
    const h = 380;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);
    // preserveDrawingBuffer: sin esto, toDataURL() sale en blanco — el
    // navegador descarta el buffer de dibujo después de presentar el frame.
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setSize(w, h);
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    contenedor.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const luzDireccional = new THREE.DirectionalLight(0xffffff, 0.6);
    luzDireccional.position.set(3, 6, 4);
    scene.add(luzDireccional);

    const grupo = new THREE.Group();
    const constructor = CONSTRUCTORES[tipo];
    const { tamano } = constructor(grupo, resultado, form);

    const envoltura = new THREE.Group();
    envoltura.add(grupo);
    scene.add(envoltura);

    const distancia = Math.max(tamano, 1.5) * 1.9 + 1;
    camera.position.set(distancia * 0.75, distancia * 0.6, distancia * 0.85);
    camera.lookAt(0, 0, 0);

    let arrastrando = false;
    let anguloY = 0.6;
    let anguloX = -0.3;
    let ultimoX = 0, ultimoY = 0;

    const onDown = (e) => { arrastrando = true; ultimoX = e.clientX; ultimoY = e.clientY; contenedor.style.cursor = "grabbing"; };
    const onUp = () => { arrastrando = false; contenedor.style.cursor = "grab"; };
    const onMove = (e) => {
      if (!arrastrando) return;
      anguloY += (e.clientX - ultimoX) * 0.008;
      anguloX += (e.clientY - ultimoY) * 0.008;
      anguloX = Math.max(-1.1, Math.min(0.3, anguloX));
      ultimoX = e.clientX;
      ultimoY = e.clientY;
    };
    contenedor.addEventListener("pointerdown", onDown);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointermove", onMove);

    let auto = 0;
    let vivo = true;
    function animar() {
      if (!vivo) return;
      requestAnimationFrame(animar);
      if (!arrastrando) auto += 0.004;
      envoltura.rotation.y = anguloY + auto;
      envoltura.rotation.x = anguloX;
      renderer.render(scene, camera);
    }
    animar();

    return () => {
      vivo = false;
      contenedor.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointermove", onMove);
      scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      });
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
      if (rendererRef.current === renderer) rendererRef.current = null;
    };
  }, [tipo, resultado, form]);

  return (
    <div>
      <div ref={contenedorRef} style={{ width: "100%", height: 380, cursor: "grab" }} />
      <p style={{ fontSize: "0.72rem", color: "var(--texto-tenue)", textAlign: "center", marginTop: 6 }}>
        Arrastra para rotar
      </p>
    </div>
  );
}

// --- Constructores de geometría por tipo ------------------------------------

function agregarEscalon(grupo, ancho, contrahuella, huella, x, yBase, z) {
  const geo = new THREE.BoxGeometry(ancho, contrahuella * 0.9, huella);
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: COLOR_ESCALON, roughness: 0.7 }));
  mesh.position.set(x, yBase + contrahuella * 0.5, z);
  grupo.add(mesh);
}

function agregarZancas(grupo, ancho, alturaTotal, largoTotal, xCentro, zCentro) {
  const geo = new THREE.BoxGeometry(0.06, alturaTotal, largoTotal * 1.02);
  const mat = new THREE.MeshStandardMaterial({ color: COLOR_ZANCA, roughness: 0.8 });
  const z1 = new THREE.Mesh(geo, mat);
  z1.position.set(xCentro + ancho / 2 + 0.03, alturaTotal / 2, zCentro);
  grupo.add(z1);
  const z2 = z1.clone();
  z2.position.x = xCentro - (ancho / 2 + 0.03);
  grupo.add(z2);
}

function construirRecta(grupo, resultado, form) {
  const { num_escalones: n, contrahuella: c, huella: hu } = resultado;
  const ancho = Number(form.ancho) || 0.9;
  const largoTotal = n * hu;
  const alturaTotal = n * c;

  for (let i = 0; i < n; i++) {
    agregarEscalon(grupo, ancho, c, hu, 0, c * i, hu * (i + 0.5));
  }
  agregarZancas(grupo, ancho, alturaTotal, largoTotal, 0, largoTotal / 2);

  grupo.position.set(0, -alturaTotal / 2, -largoTotal / 2);
  return { tamano: Math.max(largoTotal, alturaTotal) };
}

function construirL(grupo, resultado, form) {
  const { escalones_tramo1: n1, escalones_tramo2: n2, contrahuella: c, huella: hu } = resultado;
  const ancho = Number(form.ancho) || 0.9;

  // Tramo 1: sube en +z
  for (let i = 0; i < n1; i++) {
    agregarEscalon(grupo, ancho, c, hu, 0, c * i, hu * (i + 0.5));
  }
  const alturaDescanso = c * n1;
  const zDescanso = hu * n1;

  // Descanso (plataforma cuadrada)
  const geoDescanso = new THREE.BoxGeometry(ancho + hu, c * 0.9, ancho);
  const descanso = new THREE.Mesh(geoDescanso, new THREE.MeshStandardMaterial({ color: COLOR_POSTE, roughness: 0.7 }));
  descanso.position.set(hu / 2, alturaDescanso, zDescanso + ancho / 2 - hu / 2);
  grupo.add(descanso);

  // Tramo 2: gira 90°, ahora avanza en +x, mismo z fijo (junto al descanso)
  const xInicioTramo2 = ancho / 2 + 0.15;
  for (let j = 0; j < n2; j++) {
    agregarEscalon(grupo, hu, c, ancho, xInicioTramo2 + hu * (j + 0.5), alturaDescanso + c * j, zDescanso + ancho / 2 - hu / 2);
  }

  const alturaTotal = alturaDescanso + c * n2;
  const largoX = xInicioTramo2 + hu * n2;
  const largoZ = zDescanso + ancho;

  grupo.position.set(-largoX / 2, -alturaTotal / 2, -largoZ / 2);
  return { tamano: Math.max(largoX, largoZ, alturaTotal) };
}

function construirU(grupo, resultado, form) {
  const { escalones_tramo1: n1, escalones_tramo2: n2, contrahuella: c, huella: hu } = resultado;
  const ancho = Number(form.ancho) || 0.9;

  // Tramo 1: sube en +z, en x=0
  for (let i = 0; i < n1; i++) {
    agregarEscalon(grupo, ancho, c, hu, 0, c * i, hu * (i + 0.5));
  }
  const alturaDescanso = c * n1;
  const largoTramo = hu * Math.max(n1, n2);

  // Descanso a todo lo ancho, conectando los dos tramos
  const separacion = ancho + 0.15;
  const geoDescanso = new THREE.BoxGeometry(separacion + ancho, c * 0.9, ancho);
  const descanso = new THREE.Mesh(geoDescanso, new THREE.MeshStandardMaterial({ color: COLOR_POSTE, roughness: 0.7 }));
  descanso.position.set(separacion / 2, alturaDescanso, largoTramo + ancho / 2 - hu / 2);
  grupo.add(descanso);

  // Tramo 2: paralelo, baja de regreso (mismo sentido de subida pero en x desplazado)
  for (let j = 0; j < n2; j++) {
    const alturaEscalon = alturaDescanso + c * j;
    const zEscalon = largoTramo - hu * (j + 0.5);
    agregarEscalon(grupo, ancho, c, hu, separacion, alturaEscalon, zEscalon);
  }

  const alturaTotal = alturaDescanso + c * n2;
  const largoZ = largoTramo + ancho;
  const largoX = separacion + ancho;

  grupo.position.set(-largoX / 2, -alturaTotal / 2, -largoZ / 2);
  return { tamano: Math.max(largoX, largoZ, alturaTotal) };
}

function construirCaracol(grupo, resultado) {
  const { num_escalones: n, contrahuella: c, diametro_exterior: dExt, diametro_poste: dPoste, angulo_giro_total: giro } = resultado;
  const radioExt = dExt / 2;
  const radioPoste = dPoste / 2;
  const anguloEscalon = THREE.MathUtils.degToRad(giro / n);

  for (let i = 0; i < n; i++) {
    const shape = new THREE.Shape();
    const a0 = 0, a1 = anguloEscalon * 0.92; // pequeño espacio entre escalones
    shape.moveTo(radioPoste * Math.cos(a0), radioPoste * Math.sin(a0));
    shape.lineTo(radioExt * Math.cos(a0), radioExt * Math.sin(a0));
    shape.absarc(0, 0, radioExt, a0, a1, false);
    shape.lineTo(radioPoste * Math.cos(a1), radioPoste * Math.sin(a1));
    shape.absarc(0, 0, radioPoste, a1, a0, true);

    const geo = new THREE.ExtrudeGeometry(shape, { depth: c * 0.9, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2);
    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: COLOR_ESCALON, roughness: 0.7 }));
    mesh.position.y = c * i;
    mesh.rotation.y = -anguloEscalon * i;
    grupo.add(mesh);
  }

  const geoPoste = new THREE.CylinderGeometry(radioPoste, radioPoste, c * n, 20);
  const poste = new THREE.Mesh(geoPoste, new THREE.MeshStandardMaterial({ color: COLOR_POSTE, roughness: 0.6 }));
  poste.position.y = (c * n) / 2;
  grupo.add(poste);

  grupo.position.y = -(c * n) / 2;
  return { tamano: radioExt * 2.2 };
}

const CONSTRUCTORES = {
  recta: construirRecta,
  l: construirL,
  u: construirU,
  caracol: construirCaracol,
};
