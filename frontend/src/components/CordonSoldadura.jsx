import { useEffect, useRef, useState } from "react";

/**
 * Divisor de sección con forma de "cordón de soldadura" (línea punteada
 * irregular, como el rastro de un electrodo), con una chispa que se
 * enciende una vez cuando el divisor entra en pantalla.
 */
export default function CordonSoldadura() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { threshold: 0.5 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  return (
    <svg
      ref={ref}
      className={`cordon-soldadura${visible ? " visible" : ""}`}
      viewBox="0 0 1180 28"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path d="M0,14 Q30,4 60,14 T120,14 T180,14 T240,14 T300,14 T360,14 T420,14 T480,14 T540,14 T600,14 T660,14 T720,14 T780,14 T840,14 T900,14 T960,14 T1020,14 T1080,14 T1140,14 T1180,14" />
      <circle cx="590" cy="14" r="1" />
    </svg>
  );
}
