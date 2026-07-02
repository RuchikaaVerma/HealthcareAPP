"use client";

import React, { InputHTMLAttributes, SelectHTMLAttributes, ReactNode, forwardRef } from "react";
import clsx from "clsx";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({ label, error, className, ...props }, ref) => (
  <div className="flex flex-col gap-1.5">
    {label && <label className="text-sm text-clinical/70 font-body">{label}</label>}
    <input
      ref={ref}
      className={clsx(
        "bg-surface/80 border border-white/10 rounded-xl px-4 py-2.5 text-clinical placeholder:text-clinical/30",
        "focus-ring focus:border-teal/50 transition-colors font-body",
        error && "border-coral/60",
        className
      )}
      {...props}
    />
    {error && <span className="text-xs text-coral">{error}</span>}
  </div>
));
Input.displayName = "Input";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  children: ReactNode;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({ label, error, className, children, ...props }, ref) => (
  <div className="flex flex-col gap-1.5">
    {label && <label className="text-sm text-clinical/70 font-body">{label}</label>}
    <select
      ref={ref}
      className={clsx(
        "bg-surface/80 border border-white/10 rounded-xl px-4 py-2.5 text-clinical",
        "focus-ring focus:border-teal/50 transition-colors font-body",
        error && "border-coral/60",
        className
      )}
      {...props}
    >
      {children}
    </select>
    {error && <span className="text-xs text-coral">{error}</span>}
  </div>
));
Select.displayName = "Select";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({ label, error, className, ...props }, ref) => (
  <div className="flex flex-col gap-1.5">
    {label && <label className="text-sm text-clinical/70 font-body">{label}</label>}
    <textarea
      ref={ref}
      className={clsx(
        "bg-surface/80 border border-white/10 rounded-xl px-4 py-2.5 text-clinical placeholder:text-clinical/30",
        "focus-ring focus:border-teal/50 transition-colors font-body resize-none",
        error && "border-coral/60",
        className
      )}
      {...props}
    />
    {error && <span className="text-xs text-coral">{error}</span>}
  </div>
));
Textarea.displayName = "Textarea";
