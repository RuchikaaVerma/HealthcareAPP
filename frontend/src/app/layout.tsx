import type { Metadata } from "next";
import "@/styles/globals.css";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "Vitalis — Healthcare Appointment & Follow-up Manager",
  description: "Book appointments, get AI-powered symptom triage, and stay on top of your care — all in one place.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body bg-ink text-clinical min-h-screen">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
