"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { format } from "date-fns";
import GlassCard from "@/components/ui/GlassCard";
import Button from "@/components/ui/Button";
import UrgencyBadge from "@/components/ui/UrgencyBadge";
import api from "@/lib/api";
import { Calendar, Pill, FileText, X } from "lucide-react";

interface Appointment {
  id: string;
  slot_start: string;
  status: string;
  ai_urgency_level?: "Low" | "Medium" | "High";
  ai_pre_visit_failed?: number;
  ai_post_visit_summary?: string;
  ai_post_visit_failed?: number;
  prescription_text?: string;
  cancellation_reason?: string;
}

const statusLabels: Record<string, { label: string; className: string }> = {
  held: { label: "Pending confirmation", className: "text-clinical/50" },
  confirmed: { label: "Confirmed", className: "text-teal" },
  completed: { label: "Completed", className: "text-periwinkle" },
  cancelled_by_patient: { label: "Cancelled by you", className: "text-clinical/40" },
  cancelled_by_doctor: { label: "Cancelled by doctor", className: "text-coral" },
  cancelled_by_leave: { label: "Cancelled — doctor on leave", className: "text-coral" },
  no_show: { label: "No show", className: "text-clinical/40" },
};

export default function PatientAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  async function fetchAppointments() {
    setLoading(true);
    const { data } = await api.get("/api/appointments/me");
    setAppointments(data);
    setLoading(false);
  }

  useEffect(() => {
    fetchAppointments();
  }, []);

  async function handleCancel(id: string) {
    setCancellingId(id);
    try {
      await api.post(`/api/appointments/${id}/cancel`, { reason: "Cancelled by patient" });
      fetchAppointments();
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl font-semibold mb-8">My appointments</h1>

      {loading ? (
        <p className="text-clinical/50">Loading…</p>
      ) : appointments.length === 0 ? (
        <GlassCard className="text-center text-clinical/50">You haven't booked any appointments yet.</GlassCard>
      ) : (
        <div className="flex flex-col gap-5">
          {appointments.map((appt, i) => {
            const status = statusLabels[appt.status] || { label: appt.status, className: "text-clinical/50" };
            const postVisit = appt.ai_post_visit_summary ? JSON.parse(appt.ai_post_visit_summary) : null;
            const prescriptions = appt.prescription_text ? JSON.parse(appt.prescription_text) : [];
            const canCancel = ["held", "confirmed"].includes(appt.status);

            return (
              <motion.div key={appt.id} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <GlassCard>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <Calendar className="text-teal" size={20} />
                      <div>
                        <p className="font-display font-semibold">
                          {format(new Date(appt.slot_start), "EEEE, d MMMM yyyy 'at' h:mm a")}
                        </p>
                        <p className={`text-sm ${status.className}`}>{status.label}</p>
                      </div>
                    </div>
                    {appt.ai_urgency_level && <UrgencyBadge level={appt.ai_urgency_level} />}
                  </div>

                  {appt.ai_pre_visit_failed === 1 && (
                    <p className="text-xs text-clinical/40 italic mb-3">AI symptom summary was unavailable for this visit.</p>
                  )}

                  {appt.cancellation_reason && (
                    <p className="text-sm text-coral/80 mb-3">{appt.cancellation_reason}</p>
                  )}

                  {postVisit && (
                    <div className="mt-4 pt-4 border-t border-white/10 space-y-3">
                      <div className="flex items-center gap-2 text-sm font-display font-medium text-periwinkle">
                        <FileText size={15} /> Visit summary
                      </div>
                      <p className="text-sm text-clinical/70 leading-relaxed">{postVisit.summary}</p>

                      {prescriptions.length > 0 && (
                        <div className="flex items-start gap-2 text-sm text-clinical/70">
                          <Pill size={15} className="text-teal mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="font-medium text-clinical/90 mb-1">{postVisit.medication_schedule}</p>
                            <ul className="list-disc list-inside space-y-0.5 text-clinical/60">
                              {prescriptions.map((p: any, idx: number) => (
                                <li key={idx}>
                                  {p.drug_name} — {p.dosage}, {p.frequency_per_day}x/day for {p.duration_days} days
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}

                      <p className="text-sm text-clinical/60">
                        <span className="font-medium text-clinical/80">Next steps: </span>
                        {postVisit.follow_up_steps}
                      </p>

                      {appt.ai_post_visit_failed === 1 && (
                        <p className="text-xs text-clinical/40 italic">
                          AI summary unavailable — please refer to your doctor's notes directly.
                        </p>
                      )}
                    </div>
                  )}

                  {canCancel && (
                    <Button
                      variant="danger"
                      className="mt-4 !py-1.5 !px-3 text-xs"
                      onClick={() => handleCancel(appt.id)}
                      disabled={cancellingId === appt.id}
                    >
                      <X size={13} className="inline mr-1" />
                      {cancellingId === appt.id ? "Cancelling…" : "Cancel appointment"}
                    </Button>
                  )}
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
