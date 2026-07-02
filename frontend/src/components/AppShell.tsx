"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/lib/authStore";
import Navbar from "./Navbar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const hydrate = useAuthStore((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <>
      <Navbar />
      <main>{children}</main>
    </>
  );
}
