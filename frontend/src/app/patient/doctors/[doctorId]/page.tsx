"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { format, addDays } from "date-fns";
import GlassCard from "@/components/ui/GlassCard";
import Button from "@/components/ui/Button";
import { Textarea } from "@/components/ui/FormFields";
import api from "@/lib/api";
import { Calendar, Clock, AlertCircle } from "lucide-react";

interface Slot {
  slot_start: string;
  slot_end: string;
}

type Step = "pick-date" | "pick-slot" | "symptoms" | "confirmed";

export default function DoctorDetailPage() {
  const { doctorId } = useParams<{ doctorId: string }>();
  const router = useRouter();

  const [step, setStep] = useState<Step>("pick-date");
  const [selectedDate, setSelectedDate] = useState<string>(format(new Date(), "yyyy-MM-dd"));
  const [slots, setSlots] = useState<Slot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null);
  const [holdId, setHoldId] = useState<string | null>(null);
  const [symptoms, setSymptoms] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const nextSevenDays = Array.from({ length: 7 }, (_, i) => addDays(new Date(), i));

  async function fetchSlots(date: string) {
    setLoadingSlots(true);
    setError(null);
    try {
      const { data } = await api.get(`/api/doctors/${doctorId}/slots`, { params: { date } });
      setSlots(data);
    } catch {
      setError("Couldn't load availability. Please try again.");
    } finally {
      setLoadingSlots(false);
    }
  }

  useEffect(() => {
    fetchSlots(selectedDate);
  }, [selectedDate, doctorId]);

  async function handlePickSlot(slot: Slot) {
    setError(null);
    setSelectedSlot(slot);
    try {
      const { data } = await api.post("/api/appointments/hold", {
        doctor_id: doctorId,
        slot_start: slot.slot_start,
      });
      setHoldId(data.id);
      setStep("symptoms");
    } catch (err: any) {
      if (err?.response?.status === 409) {
        setError("That slot was just taken by another patient. Please pick a different time.");
        fetchSlots(selectedDate);
      } else {
        setError(err?.response?.data?.detail || "Couldn't hold that slot. Please try again.");
      }
    }
  }

  async function handleConfirm() {
    if (!holdId) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/api/appointments/confirm", {
        appointment_id: holdId,
        symptoms_text: symptoms,
      });
      setStep("confirmed");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Couldn't confirm your appointment. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <AnimatePresence mode="wait">
        {step === "pick-date" || step === "pick-slot" ? (
          <motion.div key="pick" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <h1 className="font-display text-2xl font-semibold mb-6 flex items-center gap-2">
              <Calendar className="text-teal" size={24} />
              Choose a date and time
            </h1>

            <div className="flex gap-2 mb-8 overflow-x-auto pb-2">
              {nextSevenDays.map((d) => {
                const dateStr = format(d, "yyyy-MM-dd");
                const isSelected = dateStr === selectedDate;
                return (
                  <button
                    key={dateStr}
                    onClick={() => setSelectedDate(dateStr)}
                    className={`flex-shrink-0 px-4 py-3 rounded-xl border text-sm font-display transition-colors ${
                      isSelected
                        ? "bg-teal text-ink border-teal"
                        : "bg-surface/60 border-white/10 text-clinical/70 hover:border-teal/40"
                    }`}
                  >
                    <div>{format(d, "EEE")}</div>
                    <div className="font-semibold">{format(d, "d MMM")}</div>
                  </button>
                );
              })}
            </div>

            {error && (
              <p className="text-coral text-sm mb-4 flex items-center gap-1.5">
                <AlertCircle size={14} /> {error}
              </p>
            )}

            {loadingSlots ? (
              <p className="text-clinical/50">Loading available slots…</p>
            ) : slots.length === 0 ? (
              <GlassCard className="text-center text-clinical/50">
                No slots available on this date — the doctor may be on leave or fully booked. Try another day.
              </GlassCard>
            ) : (
              <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
                {slots.map((slot) => (
                  <button
                    key={slot.slot_start}
                    onClick={() => handlePickSlot(slot)}
                    className="flex items-center justify-center gap-1.5 py-3 rounded-xl bg-surface/60 border border-white/10 text-sm font-mono text-clinical/80 hover:border-teal hover:text-teal transition-colors"
                  >
                    <Clock size={13} />
                    {format(new Date(slot.slot_start), "h:mm a")}
                  </button>
                ))}
              </div>
            )}
          </motion.div>
        ) : step === "symptoms" ? (
          <motion.div key="symptoms" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <GlassCard>
              <h1 className="font-display text-2xl font-semibold mb-2">Tell us how you're feeling</h1>
              <p className="text-clinical/60 text-sm mb-6">
                Your slot is held for the next 2 minutes. Describe your symptoms so our AI can prepare a brief for your doctor.
              </p>

              {selectedSlot && (
                <div className="mb-5 px-4 py-3 rounded-xl bg-teal/10 border border-teal/20 text-sm text-teal font-mono">
                  {format(new Date(selectedSlot.slot_start), "EEEE, d MMMM 'at' h:mm a")}
                </div>
              )}

              <Textarea
                rows={5}
                placeholder="E.g. I've had a persistent headache for 3 days, worse in the mornings, with some light sensitivity…"
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
              />

              {error && <p className="text-coral text-sm mt-3">{error}</p>}

              <div className="flex gap-3 mt-6">
                <Button variant="ghost" onClick={() => setStep("pick-date")}>
                  Back
                </Button>
                <Button onClick={handleConfirm} disabled={submitting || symptoms.trim().length < 5} className="flex-1">
                  {submitting ? "Confirming…" : "Confirm appointment"}
                </Button>
              </div>
            </GlassCard>
          </motion.div>
        ) : (
          <motion.div key="confirmed" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
            <GlassCard className="text-center py-10">
              <div className="w-16 h-16 rounded-full bg-teal/15 flex items-center justify-center mx-auto mb-5">
                <Calendar className="text-teal" size={28} />
              </div>
              <h1 className="font-display text-2xl font-semibold mb-2">Appointment confirmed</h1>
              <p className="text-clinical/60 mb-6">
                We've sent a confirmation to your email and added it to your Google Calendar (if connected).
              </p>
              <Button onClick={() => router.push("/patient/appointments")}>View my appointments</Button>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
