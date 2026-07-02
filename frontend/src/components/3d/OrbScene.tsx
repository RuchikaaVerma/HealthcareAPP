"use client";

interface OrbSceneProps {
  className?: string;
  intensity?: number;
}

export default function OrbScene({ className, intensity: _intensity }: OrbSceneProps) {
  return (
    <div
      className={className}
      style={{
        width: "100%",
        height: "100%",
        background: "rgba(19,184,166,0.06)",
        backgroundImage:
          "radial-gradient(circle at 50% 50%, rgba(19,184,166,0.15), rgba(124,156,255,0.08) 40%, transparent 70%)",
      }}
    />
  );
}