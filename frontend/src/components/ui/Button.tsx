"use client";

import { motion } from "framer-motion";
import { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  children: ReactNode;
}

export default function Button({ variant = "primary", className, children, ...props }: ButtonProps) {
  const base = "px-5 py-2.5 rounded-xl font-display font-medium text-sm transition-all focus-ring disabled:opacity-40 disabled:cursor-not-allowed";
  const variants = {
    primary: "bg-teal text-ink shadow-glow hover:bg-teal-glow",
    secondary: "bg-periwinkle/15 text-periwinkle border border-periwinkle/30 hover:bg-periwinkle/25",
    ghost: "bg-transparent text-clinical/80 hover:bg-white/5 border border-white/10",
    danger: "bg-coral/15 text-coral border border-coral/30 hover:bg-coral/25",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02, y: -1 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={clsx(base, variants[variant], className)}
      {...(props as any)}
    >
      {children}
    </motion.button>
  );
}
