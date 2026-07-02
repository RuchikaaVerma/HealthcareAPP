"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import dynamic from "next/dynamic";
import GlassCard from "@/components/ui/GlassCard";
import { Input } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";

const OrbScene = dynamic(() => import("@/components/3d/OrbScene"), { ssr: false });

export default function RegisterPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/register", { ...form, role: "patient" });
      login({
        userId: data.user_id,
        role: data.role,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        fullName: form.full_name,
      });
      router.push("/patient/doctors");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't create your account. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-[92vh] flex items-center justify-center px-6 py-12">
      <OrbScene className="absolute inset-0 w-full h-full opacity-40" intensity={0} />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md"
      >
        <GlassCard>
          <h1 className="font-display text-2xl font-semibold mb-1">Create your account</h1>
          <p className="text-clinical/60 text-sm mb-6">Book appointments and track your care in one place.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input label="Full name" required value={form.full_name} onChange={(e) => update("full_name", e.target.value)} placeholder="Jane Doe" />
            <Input label="Email" type="email" required value={form.email} onChange={(e) => update("email", e.target.value)} placeholder="you@example.com" />
            <Input label="Phone (optional)" value={form.phone} onChange={(e) => update("phone", e.target.value)} placeholder="+91 98765 43210" />
            <Input
              label="Password"
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              placeholder="At least 8 characters"
            />
            {error && <p className="text-coral text-sm">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full mt-2">
              {loading ? "Creating account…" : "Create account"}
            </Button>
          </form>

          <p className="text-center text-sm text-clinical/50 mt-6">
            Already have an account?{" "}
            <a href="/login" className="text-teal hover:underline">
              Sign in
            </a>
          </p>
        </GlassCard>
      </motion.div>
    </div>
  );
}
