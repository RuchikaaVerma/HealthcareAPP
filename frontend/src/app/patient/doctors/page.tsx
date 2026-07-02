"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import GlassCard from "@/components/ui/GlassCard";
import { Input } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import api from "@/lib/api";
import { Stethoscope, Clock } from "lucide-react";

interface Doctor {
  id: string;
  full_name: string;
  specialisation: string;
  bio?: string;
  slot_duration_minutes: number;
}

export default function DoctorSearchPage() {
  const router = useRouter();
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  async function fetchDoctors(specialisation?: string) {
    setLoading(true);
    try {
      const { data } = await api.get("/api/doctors", { params: specialisation ? { specialisation } : {} });
      setDoctors(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDoctors();
  }, []);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    fetchDoctors(search || undefined);
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl font-semibold mb-2">Find a doctor</h1>
      <p className="text-clinical/60 mb-8">Search by specialisation and book a slot that works for you.</p>

      <form onSubmit={handleSearch} className="flex gap-3 mb-10 max-w-md">
        <Input
          placeholder="e.g. Cardiology, Dermatology"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1"
        />
        <Button type="submit">Search</Button>
      </form>

      {loading ? (
        <p className="text-clinical/50">Loading doctors…</p>
      ) : doctors.length === 0 ? (
        <GlassCard className="text-center text-clinical/50">No doctors found for that specialisation yet.</GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {doctors.map((doc, i) => (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.05 }}
            >
              <GlassCard tilt className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-full bg-teal/10 flex items-center justify-center">
                    <Stethoscope className="text-teal" size={20} />
                  </div>
                  <div>
                    <h3 className="font-display font-semibold">Dr. {doc.full_name}</h3>
                    <p className="text-teal text-sm">{doc.specialisation}</p>
                  </div>
                </div>
                {doc.bio && <p className="text-clinical/60 text-sm">{doc.bio}</p>}
                <div className="flex items-center gap-1.5 text-xs text-clinical/40">
                  <Clock size={13} />
                  {doc.slot_duration_minutes} min slots
                </div>
                <Button variant="secondary" className="mt-2" onClick={() => router.push(`/patient/doctors/${doc.id}`)}>
                  View availability
                </Button>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
