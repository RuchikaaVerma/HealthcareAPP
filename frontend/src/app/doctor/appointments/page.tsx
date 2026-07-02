"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";
import GlassCard from "@/components/ui/GlassCard";
import Button from "@/components/ui/Button";
import { Textarea, Input } from "@/components/ui/FormFields";
import UrgencyBadge from "@/components/ui/UrgencyBadge";
import api from "@/lib/api";
import { Calendar, MessageSquareText, Plus, Trash2, ClipboardCheck } from "lucide-react";

interface Appointment {
  id: string;
  slot_start: string;
  status: string;
  symptoms_text?: string;
  ai_urgency_level?: "Low" | "Medium" | "High";
  ai_chief_complaint?: string;
  ai_suggested_questions?: string;
  ai_pre_visit_failed?: number;
}

interface PrescriptionRow {
  drug_name: string;
  dosage: string;
  frequency_per_day: number;
  duration_days: number;
  instructions: string;
}

const emptyRow: PrescriptionRow = { drug_name: "", dosage: "", frequency_per_day: 1, duration_days: 5, instructions: "" };

export default function DoctorAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [prescriptions, setPrescriptions] = useState<PrescriptionRow[]>([{ ...emptyRow }]);
  const [submitting, setSubmitting] = useState(false);

  async function fetchAppointments() {
    setLoading(true);
    const { data } = await api.get("/api/appointments/me");
    setAppointments(data);
    setLoading(false);
  }

  useEffect(() => {
    fetchAppointments();
  }, []);

  const upcoming = appointments.filter((a) => a.status === "confirmed");
  const past = appointments.filter((a) => !["confirmed", "held"].includes(a.status));

  function openNotesFor(id: string) {
    setActiveId(id);
    setNotes("");
    setPrescriptions([{ ...emptyRow }]);
  }

  function updateRow(idx: number, field: keyof PrescriptionRow, value: string | number) {
    setPrescriptions((rows) => rows.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));
  }

  async function handleSubmitNotes() {
    if (!activeId) return;
    setSubmitting(true);
    try {
      await api.post("/api/appointments/post-visit", {
        appointment_id: activeId,
        doctor_notes: notes,
        prescriptions: prescriptions.filter((p) => p.drug_name.trim()),
      });
      setActiveId(null);
      fetchAppointments();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl font-semibold mb-8">My schedule</h1>

      {loading ? (
        <p className="text-clinical/50">Loading…</p>
      ) : (
        <>
          <h2 className="font-display text-lg text-clinical/70 mb-4">Upcoming</h2>
          <div className="flex flex-col gap-4 mb-10">
            {upcoming.length === 0 && <GlassCard className="text-center text-clinical/50">No upcoming appointments.</GlassCard>}
            {upcoming.map((appt, i) => {
              const questions: string[] = appt.ai_suggested_questions ? JSON.parse(appt.ai_suggested_questions) : [];
              return (
                <motion.div key={appt.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                  <GlassCard>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <Calendar className="text-teal" size={20} />
                        <p className="font-display font-semibold">
                          {format(new Date(appt.slot_start), "EEEE, d MMMM 'at' h:mm a")}
                        </p>
                      </div>
                      {appt.ai_urgency_level && <UrgencyBadge level={appt.ai_urgency_level} />}
                    </div>

                    {appt.symptoms_text && (
                      <div className="mb-3">
                        <p className="text-xs text-clinical/40 uppercase tracking-wide mb-1">Patient-reported symptoms</p>
                        <p className="text-sm text-clinical/70">{appt.symptoms_text}</p>
                      </div>
                    )}

                    {appt.ai_chief_complaint && (
                      <div className="mb-3 px-4 py-3 rounded-xl bg-periwinkle/10 border border-periwinkle/20">
                        <p className="text-xs text-periwinkle uppercase tracking-wide mb-1 font-medium">AI chief complaint</p>
                        <p className="text-sm text-clinical/80">{appt.ai_chief_complaint}</p>
                      </div>
                    )}

                    {questions.length > 0 && (
                      <div className="mb-4">
                        <p className="text-xs text-clinical/40 uppercase tracking-wide mb-1.5">Suggested questions</p>
                        <ul className="list-disc list-inside text-sm text-clinical/70 space-y-1">
                          {questions.map((q, idx) => (
                            <li key={idx}>{q}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {appt.ai_pre_visit_failed === 1 && (
                      <p className="text-xs text-clinical/40 italic mb-3">AI summary unavailable — review symptoms above manually.</p>
                    )}

                    <Button variant="secondary" onClick={() => openNotesFor(appt.id)}>
                      <MessageSquareText size={15} className="inline mr-1.5" />
                      Complete visit & add notes
                    </Button>
                  </GlassCard>
                </motion.div>
              );
            })}
          </div>

          <h2 className="font-display text-lg text-clinical/70 mb-4">History</h2>
          <div className="flex flex-col gap-3">
            {past.map((appt) => (
              <GlassCard key={appt.id} className="!py-3 !px-5 flex items-center justify-between">
                <span className="text-sm text-clinical/60">{format(new Date(appt.slot_start), "d MMM yyyy, h:mm a")}</span>
                <span className="text-xs uppercase tracking-wide text-clinical/40">{appt.status.replace(/_/g, " ")}</span>
              </GlassCard>
            ))}
          </div>
        </>
      )}

      <AnimatePresence>
        {activeId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-6 z-50"
            onClick={() => setActiveId(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg"
            >
              <GlassCard className="max-h-[85vh] overflow-y-auto">
                <h2 className="font-display text-xl font-semibold mb-4 flex items-center gap-2">
                  <ClipboardCheck className="text-teal" size={20} />
                  Complete visit
                </h2>

                <Textarea
                  label="Clinical notes"
                  rows={4}
                  placeholder="Findings, diagnosis, and clinical observations…"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                />

                <div className="mt-5">
                  <p className="text-sm text-clinical/70 mb-2">Prescriptions</p>
                  {prescriptions.map((row, idx) => (
                    <div key={idx} className="grid grid-cols-2 gap-2 mb-2 p-3 rounded-xl bg-surface/40 border border-white/5">
                      <Input placeholder="Drug name" value={row.drug_name} onChange={(e) => updateRow(idx, "drug_name", e.target.value)} className="col-span-2" />
                      <Input placeholder="Dosage (e.g. 500mg)" value={row.dosage} onChange={(e) => updateRow(idx, "dosage", e.target.value)} />
                      <Input
                        type="number"
                        placeholder="Times/day"
                        value={row.frequency_per_day}
                        onChange={(e) => updateRow(idx, "frequency_per_day", Number(e.target.value))}
                      />
                      <Input
                        type="number"
                        placeholder="Duration (days)"
                        value={row.duration_days}
                        onChange={(e) => updateRow(idx, "duration_days", Number(e.target.value))}
                        className="col-span-2"
                      />
                      {prescriptions.length > 1 && (
                        <button
                          type="button"
                          onClick={() => setPrescriptions((rows) => rows.filter((_, i) => i !== idx))}
                          className="col-span-2 text-coral text-xs flex items-center gap-1 justify-end"
                        >
                          <Trash2 size={12} /> Remove
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => setPrescriptions((rows) => [...rows, { ...emptyRow }])}
                    className="text-teal text-sm flex items-center gap-1.5 mt-1"
                  >
                    <Plus size={14} /> Add another medication
                  </button>
                </div>

                <div className="flex gap-3 mt-6">
                  <Button variant="ghost" onClick={() => setActiveId(null)}>
                    Cancel
                  </Button>
                  <Button onClick={handleSubmitNotes} disabled={submitting || notes.trim().length < 5} className="flex-1">
                    {submitting ? "Saving…" : "Save & generate patient summary"}
                  </Button>
                </div>
              </GlassCard>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
