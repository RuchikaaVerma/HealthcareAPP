"use client";

import { motion } from "framer-motion";
import { ReactNode, useState } from "react";
import clsx from "clsx";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  tilt?: boolean;
  onClick?: () => void;
}

/**
 * Glassmorphic card with an optional subtle 3D tilt-on-hover effect
 * (CSS perspective transform, not a full 3D scene — keeps list views fast
 * while still carrying the platform's 3D-tactile feel).
 */
export default function GlassCard({ children, className, tilt = false, onClick }: GlassCardProps) {
  const [rotate, setRotate] = useState({ x: 0, y: 0 });

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (!tilt) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    setRotate({ x: -py * 6, y: px * 6 });
  }

  function handleMouseLeave() {
    setRotate({ x: 0, y: 0 });
  }

  return (
    <motion.div
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{
        transform: tilt ? `perspective(800px) rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)` : undefined,
        transition: "transform 0.15s ease-out",
      }}
      className={clsx("glass-panel rounded-2xl p-6", className, onClick && "cursor-pointer")}
    >
      {children}
    </motion.div>
  );
}
