"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlassCard from "@/components/ui/GlassCard";
import { Input, Select, Textarea } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import api from "@/lib/api";
import { Stethoscope, Calendar, Clock, Plus, Trash2, ShieldAlert, Check, Pencil, Trash } from "lucide-react";

interface WorkingHours {
  id?: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
}

interface Doctor {
  id: string;
  full_name: string;
  email: string;
  specialisation: string;
  bio?: string;
  slot_duration_minutes: number;
  working_hours: WorkingHours[];
}

const DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Modals state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedDoctorId, setSelectedDoctorId] = useState<string | null>(null);

  // Edit Doctor Form State
  const [editDoctor, setEditDoctor] = useState({
    id: "",
    specialisation: "",
    bio: "",
    slot_duration_minutes: 30,
  });

  // New Doctor Form State
  const [newDoctor, setNewDoctor] = useState({
    email: "",
    password: "",
    full_name: "",
    phone: "",
    specialisation: "",
    bio: "",
    slot_duration_minutes: 30,
  });

  const [workingHoursList, setWorkingHoursList] = useState<WorkingHours[]>([
    { day_of_week: 0, start_time: "09:00", end_time: "17:00" },
  ]);

  // Leave Form State
  const [leaveForm, setLeaveForm] = useState({
    start_date: "",
    end_date: "",
    reason: "",
  });

  const [submitting, setSubmitting] = useState(false);

  async function fetchDoctors() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get("/api/admin/doctors");
      setDoctors(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load doctor profiles.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDoctors();
  }, []);

  function handleAddWorkingHour() {
    setWorkingHoursList([...workingHoursList, { day_of_week: 0, start_time: "09:00", end_time: "17:00" }]);
  }

  function handleRemoveWorkingHour(index: number) {
    setWorkingHoursList(workingHoursList.filter((_, i) => i !== index));
  }

  function handleWorkingHourChange(index: number, field: keyof WorkingHours, value: any) {
    const updated = workingHoursList.map((wh, i) => {
      if (i === index) {
        return { ...wh, [field]: value };
      }
      return wh;
    });
    setWorkingHoursList(updated);
  }

  async function handleCreateDoctor(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    // Format start/end times with seconds for the backend expectation if needed (HH:MM:00)
    const formattedWorkingHours = workingHoursList.map(wh => ({
      day_of_week: Number(wh.day_of_week),
      start_time: wh.start_time.length === 5 ? `${wh.start_time}:00` : wh.start_time,
      end_time: wh.end_time.length === 5 ? `${wh.end_time}:00` : wh.end_time,
    }));

    try {
      await api.post("/api/admin/doctors", {
        ...newDoctor,
        slot_duration_minutes: Number(newDoctor.slot_duration_minutes),
        working_hours: formattedWorkingHours,
      });
      setSuccess("Doctor profile created successfully!");
      setShowAddModal(false);
      // Reset Form
      setNewDoctor({
        email: "",
        password: "",
        full_name: "",
        phone: "",
        specialisation: "",
        bio: "",
        slot_duration_minutes: 30,
      });
      setWorkingHoursList([{ day_of_week: 0, start_time: "09:00", end_time: "17:00" }]);
      fetchDoctors();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to create doctor account.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAddLeave(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedDoctorId) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await api.post(`/api/admin/doctors/${selectedDoctorId}/leave`, leaveForm);
      setSuccess("Leave successfully recorded. Impacted patients have been auto-notified!");
      setShowLeaveModal(false);
      setLeaveForm({ start_date: "", end_date: "", reason: "" });
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to submit leave conflict resolution.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteDoctor(id: string, name: string) {
    if (!window.confirm(`Are you sure you want to delete Dr. ${name}? This action cannot be undone.`)) {
      return;
    }
    setError(null);
    setSuccess(null);
    try {
      await api.delete(`/api/admin/doctors/${id}`);
      setSuccess("Doctor deleted successfully.");
      fetchDoctors();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to delete doctor.");
    }
  }

  async function handleUpdateDoctor(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      await api.patch(`/api/admin/doctors/${editDoctor.id}`, {
        specialisation: editDoctor.specialisation,
        bio: editDoctor.bio,
        slot_duration_minutes: Number(editDoctor.slot_duration_minutes),
      });
      setSuccess("Doctor profile updated successfully!");
      setShowEditModal(false);
      fetchDoctors();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to update doctor.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h1 className="font-display text-3xl font-semibold mb-2">Manage Doctors</h1>
          <p className="text-clinical/60">Create doctor profiles, manage working hours, and resolve leave schedules.</p>
        </div>
        <Button onClick={() => setShowAddModal(true)} className="flex items-center gap-2">
          <Plus size={16} /> Add Doctor
        </Button>
      </div>

      {success && (
        <div className="mb-6 p-4 rounded-xl bg-teal/10 border border-teal/20 text-teal flex items-center gap-2 text-sm">
          <Check size={16} /> {success}
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-coral/10 border border-coral/20 text-coral flex items-center gap-2 text-sm">
          <ShieldAlert size={16} /> {error}
        </div>
      )}

      {loading ? (
        <p className="text-clinical/50">Loading doctor directory...</p>
      ) : doctors.length === 0 ? (
        <GlassCard className="text-center py-12 text-clinical/50">
          No doctor profiles registered yet. Click "Add Doctor" above to get started.
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {doctors.map((doc) => (
            <GlassCard key={doc.id} className="flex flex-col gap-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-teal/10 flex items-center justify-center">
                    <Stethoscope className="text-teal" size={22} />
                  </div>
                  <div>
                    <h3 className="font-display text-lg font-semibold">Dr. {doc.full_name}</h3>
                    <p className="text-teal text-sm">{doc.specialisation}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    className="!px-2 !py-1.5 text-xs text-clinical/70 hover:text-teal"
                    onClick={() => {
                      setEditDoctor({
                        id: doc.id,
                        specialisation: doc.specialisation,
                        bio: doc.bio || "",
                        slot_duration_minutes: doc.slot_duration_minutes,
                      });
                      setShowEditModal(true);
                    }}
                    title="Edit Doctor"
                  >
                    <Pencil size={14} />
                  </Button>
                  <Button
                    variant="ghost"
                    className="!px-2 !py-1.5 text-xs text-clinical/70 hover:text-coral"
                    onClick={() => handleDeleteDoctor(doc.id, doc.full_name)}
                    title="Delete Doctor"
                  >
                    <Trash size={14} />
                  </Button>
                  <Button
                    variant="danger"
                    className="!px-3 !py-1.5 text-xs"
                    onClick={() => {
                      setSelectedDoctorId(doc.id);
                      setShowLeaveModal(true);
                    }}
                  >
                    <Calendar size={13} className="inline mr-1" />
                    Mark Leave
                  </Button>
                </div>
              </div>

              {doc.bio && <p className="text-clinical/70 text-sm leading-relaxed">{doc.bio}</p>}

              <div className="border-t border-white/5 pt-3">
                <p className="text-xs text-clinical/40 uppercase tracking-wider mb-2 font-medium">Availability Template</p>
                <div className="grid grid-cols-2 gap-2 text-xs text-clinical/75">
                  <span className="flex items-center gap-1.5">
                    <Clock size={13} className="text-teal" /> {doc.slot_duration_minutes} min slots
                  </span>
                  <span>{doc.email}</span>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {doc.working_hours && doc.working_hours.length > 0 ? (
                    doc.working_hours.map((wh, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-surface/50 border border-white/5 text-[11px]"
                      >
                        {DAYS_OF_WEEK[wh.day_of_week]}: {wh.start_time.substring(0, 5)} - {wh.end_time.substring(0, 5)}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-coral italic">No availability slots defined</span>
                  )}
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      {/* Add Doctor Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-6 z-50 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-2xl my-8"
            >
              <GlassCard className="max-h-[90vh] overflow-y-auto">
                <h2 className="font-display text-xl font-semibold mb-4">Register New Doctor</h2>
                <form onSubmit={handleCreateDoctor} className="flex flex-col gap-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Full Name"
                      required
                      placeholder="e.g. Ruhi Sharma"
                      value={newDoctor.full_name}
                      onChange={(e) => setNewDoctor({ ...newDoctor, full_name: e.target.value })}
                    />
                    <Input
                      label="Email"
                      type="email"
                      required
                      placeholder="e.g. dr.ruhi@clinic.com"
                      value={newDoctor.email}
                      onChange={(e) => setNewDoctor({ ...newDoctor, email: e.target.value })}
                    />
                    <Input
                      label="Password"
                      type="password"
                      required
                      minLength={8}
                      placeholder="Min 8 characters"
                      value={newDoctor.password}
                      onChange={(e) => setNewDoctor({ ...newDoctor, password: e.target.value })}
                    />
                    <Input
                      label="Phone"
                      placeholder="e.g. +91 9876543210"
                      value={newDoctor.phone}
                      onChange={(e) => setNewDoctor({ ...newDoctor, phone: e.target.value })}
                    />
                    <Input
                      label="Specialisation"
                      required
                      placeholder="e.g. Cardiology, Pediatrics"
                      value={newDoctor.specialisation}
                      onChange={(e) => setNewDoctor({ ...newDoctor, specialisation: e.target.value })}
                    />
                    <Input
                      label="Slot Duration (minutes)"
                      type="number"
                      required
                      value={newDoctor.slot_duration_minutes}
                      onChange={(e) => setNewDoctor({ ...newDoctor, slot_duration_minutes: Number(e.target.value) })}
                    />
                  </div>

                  <Textarea
                    label="Doctor Biography"
                    rows={3}
                    placeholder="Short description of experience, credentials, etc."
                    value={newDoctor.bio}
                    onChange={(e) => setNewDoctor({ ...newDoctor, bio: e.target.value })}
                  />

                  {/* Working Hours Builder */}
                  <div className="border-t border-white/5 pt-4 mt-2">
                    <div className="flex justify-between items-center mb-3">
                      <p className="text-sm font-medium text-clinical/85">Configure Weekly Availability</p>
                      <Button
                        type="button"
                        variant="secondary"
                        className="!px-3 !py-1 text-xs"
                        onClick={handleAddWorkingHour}
                      >
                        Add Slot
                      </Button>
                    </div>

                    <div className="flex flex-col gap-2 max-h-[150px] overflow-y-auto pr-1">
                      {workingHoursList.map((wh, idx) => (
                        <div key={idx} className="flex gap-2 items-center bg-surface/30 p-2 rounded-xl border border-white/5">
                          <Select
                            value={wh.day_of_week}
                            onChange={(e) => handleWorkingHourChange(idx, "day_of_week", Number(e.target.value))}
                            className="flex-1 !py-1.5"
                          >
                            {DAYS_OF_WEEK.map((day, dIdx) => (
                              <option key={dIdx} value={dIdx}>
                                {day}
                              </option>
                            ))}
                          </Select>
                          <Input
                            type="time"
                            value={wh.start_time}
                            onChange={(e) => handleWorkingHourChange(idx, "start_time", e.target.value)}
                            className="!py-1.5"
                          />
                          <span className="text-clinical/40 text-xs">to</span>
                          <Input
                            type="time"
                            value={wh.end_time}
                            onChange={(e) => handleWorkingHourChange(idx, "end_time", e.target.value)}
                            className="!py-1.5"
                          />
                          {workingHoursList.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveWorkingHour(idx)}
                              className="text-coral p-1.5 hover:bg-coral/10 rounded-lg transition-colors"
                            >
                              <Trash2 size={15} />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-3 justify-end mt-4">
                    <Button type="button" variant="ghost" onClick={() => setShowAddModal(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={submitting}>
                      {submitting ? "Creating..." : "Create Profile"}
                    </Button>
                  </div>
                </form>
              </GlassCard>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Leave Schedule Modal */}
      <AnimatePresence>
        {showLeaveModal && (
          <div className="fixed inset-0 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-6 z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md"
            >
              <GlassCard>
                <h2 className="font-display text-xl font-semibold mb-4">Mark Doctor on Leave</h2>
                <p className="text-xs text-coral mb-4">
                  * Warning: Existing patient appointments during this period will be auto-cancelled and patients notified.
                </p>
                <form onSubmit={handleAddLeave} className="flex flex-col gap-4">
                  <Input
                    label="Start Date"
                    type="date"
                    required
                    value={leaveForm.start_date}
                    onChange={(e) => setLeaveForm({ ...leaveForm, start_date: e.target.value })}
                  />
                  <Input
                    label="End Date"
                    type="date"
                    required
                    value={leaveForm.end_date}
                    onChange={(e) => setLeaveForm({ ...leaveForm, end_date: e.target.value })}
                  />
                  <Textarea
                    label="Reason"
                    rows={2}
                    placeholder="e.g. Medical Conference, Annual Leave"
                    value={leaveForm.reason}
                    onChange={(e) => setLeaveForm({ ...leaveForm, reason: e.target.value })}
                  />

                  <div className="flex gap-3 justify-end mt-4">
                    <Button type="button" variant="ghost" onClick={() => setShowLeaveModal(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={submitting}>
                      {submitting ? "Submitting..." : "Schedule Leave"}
                    </Button>
                  </div>
                </form>
              </GlassCard>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Edit Doctor Modal */}
      <AnimatePresence>
        {showEditModal && (
          <div className="fixed inset-0 bg-ink/80 backdrop-blur-sm flex items-center justify-center p-6 z-50 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-lg my-8"
            >
              <GlassCard>
                <h2 className="font-display text-xl font-semibold mb-4">Edit Doctor Profile</h2>
                <form onSubmit={handleUpdateDoctor} className="flex flex-col gap-4">
                  <Input
                    label="Specialisation"
                    required
                    value={editDoctor.specialisation}
                    onChange={(e) => setEditDoctor({ ...editDoctor, specialisation: e.target.value })}
                  />
                  <Input
                    label="Slot Duration (minutes)"
                    type="number"
                    required
                    value={editDoctor.slot_duration_minutes}
                    onChange={(e) => setEditDoctor({ ...editDoctor, slot_duration_minutes: Number(e.target.value) })}
                  />
                  <Textarea
                    label="Doctor Biography"
                    rows={3}
                    value={editDoctor.bio}
                    onChange={(e) => setEditDoctor({ ...editDoctor, bio: e.target.value })}
                  />

                  <div className="flex gap-3 justify-end mt-4">
                    <Button type="button" variant="ghost" onClick={() => setShowEditModal(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={submitting}>
                      {submitting ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                </form>
              </GlassCard>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
