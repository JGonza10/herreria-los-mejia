import { useEffect, useImperativeHandle, useRef } from "react";
import * as THREE from "three";

// 3D paramétrico genérico para el resto del catálogo (Fase 6) — mismo
// patrón que Escalera3D.jsx: un constructor por modo_dibujo, recibiendo la
// especificación unificada de pieza (dominio/spec.py) en vez de un
// resultado de escalera.

const COLOR_MARCO = 0x2b2620;
const COLOR_BARROTE = 0xd85a30;
const COLOR_ALUMINIO = 0xb9b6ac;
const COLOR_VIDRIO = 0x9fd0e0;
const SEPARACION_BARROTES_DEFAULT_M = 0.12;

export default function Pieza3D({ spec, modoDibujo = "barrotes", capturaRef }) {
  const contenedorRef = useRef(null);
  const rendererRef = useRef(null);

  useImperativeHandle(capturaRef, () => ({
    capturar: () => rendererRef.current?.domElement.toDataURL("image/png") ?? null,
  }), []);

  useEffect(() => {
    const contenedor = contenedorRef.current;
    if (!contenedor || !spec?.medidas?.ancho_m || !spec?.medidas?.alto_m) return;

    const w = contenedor.clientWidth;
    const h = 320;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 100);
    // preserveDrawingBuffer: para poder capturar el canvas igual que en
    // Escalera3D.jsx (ver README, sección de la ficha de escalera).
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
    const constructor = CONSTRUCTORES[modoDibujo] || CONSTRUCTORES.barrotes;
    const { tamano } = constructor(grupo, spec);
    scene.add(grupo);

    const distanciaBase = Math.max(tamano, 1.5) * 1.9 + 1;

    let arrastrando = false;
    let anguloY = 0.5;
    let anguloX = -0.15;
    let ultimoX = 0, ultimoY = 0;
    let zoom = 1;

    const onDown = (e) => { arrastrando = true; ultimoX = e.clientX; ultimoY = e.clientY; contenedor.style.cursor = "grabbing"; };
    const onUp = () => { arrastrando = false; contenedor.style.cursor = "grab"; };
    const onMove = (e) => {
      if (!arrastrando) return;
      anguloY += (e.clientX - ultimoX) * 0.008;
      anguloX += (e.clientY - ultimoY) * 0.008;
      anguloX = Math.max(-1.1, Math.min(0.6, anguloX));
      ultimoX = e.clientX;
      ultimoY = e.clientY;
    };
    // Zoom con la rueda del ratón.
    const onWheel = (e) => {
      e.preventDefault();
      zoom = Math.max(0.4, Math.min(2.5, zoom + e.deltaY * 0.0015));
    };
    // Gesto de pinza en móvil: dos dedos acercándose/alejándose hacen zoom
    // — en un teléfono la gente intenta hacer pinza por instinto.
    let distanciaInicialPinza = null;
    const distanciaEntreToques = (touches) => {
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.hypot(dx, dy);
    };
    const onTouchStart = (e) => {
      if (e.touches.length === 2) distanciaInicialPinza = distanciaEntreToques(e.touches);
    };
    const onTouchMove = (e) => {
      if (e.touches.length === 2 && distanciaInicialPinza) {
        e.preventDefault();
        const actual = distanciaEntreToques(e.touches);
        zoom = Math.max(0.4, Math.min(2.5, zoom * (distanciaInicialPinza / actual)));
        distanciaInicialPinza = actual;
      }
    };
    const onTouchEnd = () => { distanciaInicialPinza = null; };

    contenedor.addEventListener("pointerdown", onDown);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointermove", onMove);
    contenedor.addEventListener("wheel", onWheel, { passive: false });
    contenedor.addEventListener("touchstart", onTouchStart, { passive: true });
    contenedor.addEventListener("touchmove", onTouchMove, { passive: false });
    contenedor.addEventListener("touchend", onTouchEnd);

    let vivo = true;
    function animar() {
      if (!vivo) return;
      requestAnimationFrame(animar);
      grupo.rotation.y = anguloY;
      grupo.rotation.x = anguloX;
      const distancia = distanciaBase * zoom;
      camera.position.set(distancia * 0.6, distancia * 0.35, distancia * 0.9);
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    }
    animar();

    return () => {
      vivo = false;
      contenedor.removeEventListener("pointerdown", onDown);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointermove", onMove);
      contenedor.removeEventListener("wheel", onWheel);
      contenedor.removeEventListener("touchstart", onTouchStart);
      contenedor.removeEventListener("touchmove", onTouchMove);
      contenedor.removeEventListener("touchend", onTouchEnd);
      scene.traverse((obj) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      });
      renderer.dispose();
      if (renderer.domElement.parentNode) renderer.domElement.parentNode.removeChild(renderer.domElement);
      if (rendererRef.current === renderer) rendererRef.current = null;
    };
  }, [spec, modoDibujo]);

  return (
    <div>
      <div ref={contenedorRef} style={{ width: "100%", height: 320, cursor: "grab", touchAction: "none" }} />
      <p style={{ fontSize: "0.72rem", color: "var(--texto-tenue)", textAlign: "center", marginTop: 6 }}>
        Arrastra para rotar · rueda o pinza para zoom
      </p>
    </div>
  );
}

// --- Constructores de geometría por modo_dibujo -----------------------------

function marcoPerimetral(grupo, ancho, alto, grosor, material) {
  const superior = new THREE.Mesh(new THREE.BoxGeometry(ancho, grosor, grosor), material);
  superior.position.set(0, alto / 2, 0);
  grupo.add(superior);

  const inferior = superior.clone();
  inferior.position.set(0, -alto / 2, 0);
  grupo.add(inferior);

  const izquierdo = new THREE.Mesh(new THREE.BoxGeometry(grosor, alto, grosor), material);
  izquierdo.position.set(-ancho / 2, 0, 0);
  grupo.add(izquierdo);

  const derecho = izquierdo.clone();
  derecho.position.set(ancho / 2, 0, 0);
  grupo.add(derecho);
}

function construirBarrotes(grupo, spec) {
  const { ancho_m: ancho, alto_m: alto } = spec.medidas;
  const grosor = 0.04;
  const materialMarco = new THREE.MeshStandardMaterial({ color: COLOR_MARCO, roughness: 0.7 });
  marcoPerimetral(grupo, ancho, alto, grosor, materialMarco);

  const separacionM = (spec.estructura?.separacion_barrotes_cm || SEPARACION_BARROTES_DEFAULT_M * 100) / 100;
  const numBarrotes = Math.max(0, Math.round(ancho / separacionM) - 1);
  const materialBarrote = new THREE.MeshStandardMaterial({ color: COLOR_BARROTE, roughness: 0.7 });

  for (let i = 1; i <= numBarrotes; i++) {
    const x = -ancho / 2 + (ancho / (numBarrotes + 1)) * i;
    const barrote = new THREE.Mesh(new THREE.BoxGeometry(grosor * 0.7, alto - grosor * 2, grosor * 0.7), materialBarrote);
    barrote.position.set(x, 0, 0);
    grupo.add(barrote);
  }

  const travesanos = spec.estructura?.travesanos || 0;
  for (let i = 1; i <= travesanos; i++) {
    const y = -alto / 2 + (alto / (travesanos + 1)) * i;
    const travesano = new THREE.Mesh(new THREE.BoxGeometry(ancho, grosor * 0.8, grosor * 0.8), materialBarrote);
    travesano.position.set(0, y, 0);
    grupo.add(travesano);
  }

  return { tamano: Math.max(ancho, alto) };
}

function construirCancel(grupo, spec) {
  const { ancho_m: ancho, alto_m: alto } = spec.medidas;
  const grosor = 0.05;
  const materialAluminio = new THREE.MeshStandardMaterial({ color: COLOR_ALUMINIO, roughness: 0.4, metalness: 0.6 });
  marcoPerimetral(grupo, ancho, alto, grosor, materialAluminio);

  // Cristal con transparencia real (MeshPhysicalMaterial + transmission),
  // no un color plano — se nota la diferencia con la luz de la escena.
  const materialVidrio = new THREE.MeshPhysicalMaterial({
    color: COLOR_VIDRIO, transparent: true, opacity: 0.35, roughness: 0.05, transmission: 0.6, metalness: 0,
  });

  const divisiones = spec.estructura?.divisiones_verticales || 0;
  const numPaneles = divisiones + 1;
  const anchoPanel = ancho / numPaneles;

  for (let i = 0; i < numPaneles; i++) {
    const x = -ancho / 2 + anchoPanel * (i + 0.5);
    const vidrio = new THREE.Mesh(new THREE.BoxGeometry(anchoPanel - grosor, alto - grosor * 2, grosor * 0.3), materialVidrio);
    vidrio.position.set(x, 0, 0);
    grupo.add(vidrio);

    if (i > 0) {
      const division = new THREE.Mesh(new THREE.BoxGeometry(grosor * 0.6, alto - grosor * 2, grosor), materialAluminio);
      division.position.set(-ancho / 2 + anchoPanel * i, 0, 0);
      grupo.add(division);
    }
  }

  return { tamano: Math.max(ancho, alto) };
}

function construirVidrio(grupo, spec) {
  const { ancho_m: ancho, alto_m: alto } = spec.medidas;
  const grosor = 0.03;
  const materialMarco = new THREE.MeshStandardMaterial({ color: COLOR_ALUMINIO, roughness: 0.4, metalness: 0.5 });
  marcoPerimetral(grupo, ancho, alto, grosor, materialMarco);

  const materialVidrio = new THREE.MeshPhysicalMaterial({
    color: COLOR_VIDRIO, transparent: true, opacity: 0.3, roughness: 0.05, transmission: 0.7, metalness: 0,
  });
  const vidrio = new THREE.Mesh(new THREE.BoxGeometry(ancho - grosor * 2, alto - grosor * 2, grosor), materialVidrio);
  grupo.add(vidrio);

  return { tamano: Math.max(ancho, alto) };
}

function construirEstructura(grupo, spec) {
  // Barandal: por convención ancho_m guarda la longitud (metro lineal) y
  // alto_m la altura de referencia — ver dominio/precios.py, cotizar_partida.
  const { ancho_m: longitud, alto_m: altura } = spec.medidas;
  const grosor = 0.035;
  const material = new THREE.MeshStandardMaterial({ color: COLOR_MARCO, roughness: 0.7 });

  const pasamanos = new THREE.Mesh(new THREE.BoxGeometry(longitud, grosor, grosor), material);
  pasamanos.position.set(0, altura / 2, 0);
  grupo.add(pasamanos);

  const separacionPostes = 1.0;
  const numPostes = Math.max(2, Math.round(longitud / separacionPostes) + 1);
  for (let i = 0; i < numPostes; i++) {
    const x = -longitud / 2 + (longitud / (numPostes - 1)) * i;
    const poste = new THREE.Mesh(new THREE.BoxGeometry(grosor, altura, grosor), material);
    poste.position.set(x, 0, 0);
    grupo.add(poste);
  }

  return { tamano: Math.max(longitud, altura) };
}

const CONSTRUCTORES = {
  barrotes: construirBarrotes,
  cancel: construirCancel,
  vidrio: construirVidrio,
  estructura: construirEstructura,
};
