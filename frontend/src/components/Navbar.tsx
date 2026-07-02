"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/authStore";
import { Activity, LogOut } from "lucide-react";
import Button from "./ui/Button";

export default function Navbar() {
  const { isAuthenticated, role, fullName, logout } = useAuthStore();
  const pathname = usePathname();
  const router = useRouter();

  const roleLinks: Record<string, { href: string; label: string }[]> = {
    patient: [
      { href: "/patient/doctors", label: "Find a doctor" },
      { href: "/patient/appointments", label: "My appointments" },
    ],
    doctor: [
      { href: "/doctor/appointments", label: "My schedule" },
    ],
    admin: [
      { href: "/admin/doctors", label: "Manage doctors" },
    ],
  };

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-white/5">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-display text-lg font-semibold">
          <Activity className="text-teal" size={22} />
          <span className="text-gradient-teal">Vitalis</span>
        </Link>

        <div className="flex items-center gap-6">
          {isAuthenticated &&
            role &&
            roleLinks[role]?.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-body transition-colors ${
                  pathname === link.href ? "text-teal" : "text-clinical/70 hover:text-clinical"
                }`}
              >
                {link.label}
              </Link>
            ))}

          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-clinical/60 hidden sm:inline">{fullName}</span>
              <Button variant="ghost" onClick={handleLogout} className="!px-3 !py-2">
                <LogOut size={16} />
              </Button>
            </div>
          ) : (
            <Link href="/login">
              <Button variant="primary">Sign in</Button>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
