"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Button from "@/components/ui/Button";
import GlassCard from "@/components/ui/GlassCard";
import { Stethoscope, CalendarCheck, Brain, Bell, ShieldCheck } from "lucide-react";

const features = [
  {
    icon: CalendarCheck,
    title: "Book without the back-and-forth",
    body: "Search doctors by specialisation, see real availability, and hold your slot the instant you pick it — no double-bookings, ever.",
  },
  {
    icon: Brain,
    title: "Your symptoms, understood before you arrive",
    body: "Describe how you're feeling and our AI prepares a structured brief — urgency, chief complaint, and questions worth asking — for your doctor.",
  },
  {
    icon: Stethoscope,
    title: "Visit notes you can actually read",
    body: "After your visit, clinical notes are turned into a plain-language summary with your medication schedule and next steps.",
  },
  {
    icon: Bell,
    title: "Reminders that keep you on track",
    body: "Medication reminders land in your inbox exactly when each dose is due, for as long as your prescription runs.",
  },
];

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* ---- Hero ---- */}
      <section className="relative h-[92vh] flex items-center justify-center">
        <div className="absolute inset-0 bg-radial-fade pointer-events-none" />

        <div className="relative z-10 max-w-3xl mx-auto text-center px-6">
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-teal font-mono text-sm tracking-widest uppercase mb-4"
          >
            Care, coordinated
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="font-display text-5xl sm:text-6xl font-semibold leading-[1.05] mb-6"
          >
            Every appointment, <span className="text-gradient-teal">understood</span> before it begins.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-clinical/70 text-lg mb-10 max-w-xl mx-auto"
          >
            Vitalis books your visit, briefs your doctor on your symptoms with AI,
            and turns the visit into a summary you'll actually understand.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex items-center justify-center gap-4"
          >
            <Link href="/register">
              <Button variant="primary" className="!px-7 !py-3 text-base">Book your first visit</Button>
            </Link>
            <Link href="/login">
              <Button variant="ghost" className="!px-7 !py-3 text-base">Sign in</Button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ---- Features ---- */}
      <section className="relative max-w-6xl mx-auto px-6 py-24">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
            >
              <GlassCard tilt className="h-full">
                <f.icon className="text-teal mb-4" size={28} />
                <h3 className="font-display text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-clinical/60 text-sm leading-relaxed">{f.body}</p>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ---- Trust strip ---- */}
      <section className="relative max-w-4xl mx-auto px-6 pb-24 text-center">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="flex items-center justify-center gap-2 text-clinical/50 text-sm"
        >
          <ShieldCheck size={16} className="text-teal" />
          Role-based access keeps patient, doctor, and admin data separated and secure.
        </motion.div>
      </section>
    </div>
  );
}
