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

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await api.post("/api/auth/login", { email, password });
      const me = await api.get("/api/auth/me", { headers: { Authorization: `Bearer ${data.access_token}` } });
      login({
        userId: data.user_id,
        role: data.role,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        fullName: me.data.full_name,
      });
      const destinations: Record<string, string> = {
        patient: "/patient/doctors",
        doctor: "/doctor/appointments",
        admin: "/admin/doctors",
      };
      router.push(destinations[data.role] || "/");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't sign in. Check your details and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-[90vh] flex items-center justify-center px-6">
      <OrbScene className="absolute inset-0 w-full h-full opacity-40" intensity={0} />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md"
      >
        <GlassCard>
          <h1 className="font-display text-2xl font-semibold mb-1">Welcome back</h1>
          <p className="text-clinical/60 text-sm mb-6">Sign in to manage your appointments.</p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
            {error && <p className="text-coral text-sm">{error}</p>}
            <Button type="submit" disabled={loading} className="w-full mt-2">
              {loading ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="text-center text-sm text-clinical/50 mt-6">
            New here?{" "}
            <a href="/register" className="text-teal hover:underline">
              Create a patient account
            </a>
          </p>
        </GlassCard>
      </motion.div>
    </div>
  );
}
