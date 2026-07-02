"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

interface VitalsOrbProps {
  /** 0 = calm idle pulse, 1 = fast urgent pulse (e.g. when showing a High urgency AI summary) */
  intensity?: number;
  color?: string;
}

/**
 * The platform's signature visual: a wireframe sphere with a glowing ECG-style
 * waveform traced around its equator, like a heartbeat wrapped around a globe.
 * Rotates slowly and ambiently; pulse speed/amplitude responds to `intensity`
 * so the same component can sit calm on the landing page and "spike" when
 * showing an urgent AI triage result.
 */
export default function VitalsOrb({ intensity = 0, color = "#13B8A6" }: VitalsOrbProps) {
  const groupRef = useRef<THREE.Group>(null);
  const lineRef = useRef<THREE.Line>(null);
  const materialRef = useRef<THREE.LineBasicMaterial>(null);

  const { geometry, basePositions } = useMemo(() => {
    const segments = 256;
    const radius = 1.6;
    const positions = new Float32Array(segments * 3);
    for (let i = 0; i < segments; i++) {
      const theta = (i / segments) * Math.PI * 2;
      positions[i * 3] = Math.cos(theta) * radius;
      positions[i * 3 + 1] = 0;
      positions[i * 3 + 2] = Math.sin(theta) * radius;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return { geometry: geo, basePositions: positions.slice() };
  }, []);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (groupRef.current) {
      groupRef.current.rotation.y = t * 0.15;
      groupRef.current.rotation.x = Math.sin(t * 0.1) * 0.1;
    }
    if (lineRef.current) {
      const posAttr = lineRef.current.geometry.attributes.position as THREE.BufferAttribute;
      const speed = 1.4 + intensity * 2.5;
      const amplitude = 0.08 + intensity * 0.22;
      for (let i = 0; i < posAttr.count; i++) {
        const x = basePositions[i * 3];
        const z = basePositions[i * 3 + 2];
        const theta = Math.atan2(z, x);
        // ECG-like spike pattern: sharp pulses at intervals, flat between
        const pulsePhase = (theta * 3 + t * speed) % (Math.PI * 2);
        const spike = Math.exp(-Math.pow((pulsePhase - Math.PI) * 4, 2)) * amplitude * 4;
        posAttr.array[i * 3 + 1] = spike - amplitude * 0.5;
      }
      posAttr.needsUpdate = true;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Wireframe sphere shell */}
      <mesh>
        <icosahedronGeometry args={[1.6, 2]} />
        <meshBasicMaterial color={color} wireframe transparent opacity={0.18} />
      </mesh>

      {/* Inner glow sphere */}
      <mesh>
        <sphereGeometry args={[1.3, 32, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.06} />
      </mesh>

      {/* ECG pulse ring */}
      <primitive object={new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, linewidth: 2 }))} ref={lineRef} />

      {/* A second ring rotated for depth */}
      <group rotation={[Math.PI / 2.3, 0, 0]}>
        <mesh>
          <ringGeometry args={[1.58, 1.6, 64]} />
          <meshBasicMaterial color={color} transparent opacity={0.3} side={THREE.DoubleSide} />
        </mesh>
      </group>

      <pointLight color={color} intensity={2} distance={6} />
    </group>
  );
}