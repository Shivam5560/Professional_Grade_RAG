"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

const fragment = `
  uniform float uTime;
  varying vec2 vUv;
  void main() {
    vec2 p = vUv - .5;
    float radius = length(p);
    float wave = sin(radius * 28.0 - uTime * .55) * .5 + .5;
    float mintField = smoothstep(.55, .04, radius) * (.22 + wave * .12);
    float copperField = smoothstep(.28, .0, distance(vUv, vec2(.76,.22))) * .2;
    vec3 mint = vec3(.718,.984,.843);
    vec3 copper = vec3(.894,.604,.404);
    vec3 color = mint * mintField + copper * copperField;
    gl_FragColor = vec4(color, min(.34, mintField + copperField));
  }
`;

export default function CinematicScene({ active }: { active: boolean }) {
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!active || !host) return;

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setClearColor(0x000000, 0);
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const geometry = new THREE.PlaneGeometry(2, 2);
    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: { uTime: { value: 0 } },
      vertexShader:
        "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,1.0);}",
      fragmentShader: fragment,
    });
    scene.add(new THREE.Mesh(geometry, material));

    let frame = 0;
    let intersecting = false;

    const shouldRender = () =>
      intersecting && document.visibilityState === "visible";
    const render = (time: number) => {
      material.uniforms.uTime.value = time / 1000;
      renderer.render(scene, camera);
      frame = shouldRender() ? requestAnimationFrame(render) : 0;
    };
    const syncAnimation = () => {
      if (shouldRender() && frame === 0) {
        frame = requestAnimationFrame(render);
      } else if (!shouldRender() && frame !== 0) {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    };

    const intersection = new IntersectionObserver(
      ([entry]) => {
        intersecting = entry.isIntersecting;
        syncAnimation();
      },
      { threshold: 0.05 },
    );
    intersection.observe(host);
    document.addEventListener("visibilitychange", syncAnimation);

    const resize = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      renderer.setSize(width, height, false);
    });
    resize.observe(host);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      document.removeEventListener("visibilitychange", syncAnimation);
      intersection.disconnect();
      resize.disconnect();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    };
  }, [active]);

  return (
    <div
      ref={hostRef}
      aria-hidden
      className="pointer-events-none absolute inset-0"
    />
  );
}
