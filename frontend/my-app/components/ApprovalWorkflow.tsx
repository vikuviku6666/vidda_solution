"use client";

import { useState, useEffect } from "react";
import axios from "axios";

type Stage = "recommendation" | "review" | "edit" | "published";

interface Props {
  planId: string;
  onPlanUpdated: () => void;
}

interface Notification {
  type: "success" | "error" | "info";
  message: string;
}

export default function ApprovalWorkflow({ planId, onPlanUpdated }: Props) {
  const [stage, setStage] = useState<Stage>("recommendation");
  const [notes, setNotes] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [showEditBox, setShowEditBox] = useState(false);
  const [notification, setNotification] = useState<Notification | null>(null);

  // Auto-dismiss notification after 4 seconds
  useEffect(() => {
    if (!notification) return;
    const t = setTimeout(() => setNotification(null), 4000);
    return () => clearTimeout(t);
  }, [notification]);

  const notify = (type: Notification["type"], message: string) =>
    setNotification({ type, message });

  const handleEdit = () => {
    setShowEditBox(true);
    setNotification(null);
  };

  const handleRevise = async () => {
    if (!notes.trim()) {
      notify("error", "Please enter your feedback before submitting.");
      return;
    }

    setIsProcessing(true);
    setNotification(null);
    try {
      await axios.post(`http://127.0.0.1:8000/workflow/revise/${planId}`, {
        feedback: notes,
      });
      notify("success", "Training plan has been revised based on your feedback!");
      setNotes("");
      setShowEditBox(false);
      onPlanUpdated();
      setStage("recommendation");
    } catch (err: any) {
      notify(
        "error",
        "Error revising plan: " + (err.response?.data?.detail || err.message)
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async () => {
    setIsProcessing(true);
    setNotification(null);
    try {
      await axios.patch(`http://127.0.0.1:8000/training/plans/${planId}`, {
        status: "approved",
        reviewer_notes: "Approved",
      });
      notify("success", "Plan approved and queued for LMS export!");
      setStage("published");
    } catch (err: any) {
      notify(
        "error",
        "Error approving plan: " + (err.response?.data?.detail || err.message)
      );
    } finally {
      setIsProcessing(false);
    }
  };

  const notificationColors = {
    success: "bg-emerald-50 border-emerald-300 text-emerald-800",
    error:   "bg-red-50 border-red-300 text-red-800",
    info:    "bg-blue-50 border-blue-300 text-blue-800",
  };

  const notificationIcons = {
    success: "✅",
    error:   "❌",
    info:    "ℹ️",
  };

  return (
    <div className="w-full rounded-lg border bg-card p-6 shadow-sm space-y-4">

      {/* Inline notification */}
      {notification && (
        <div
          className={`flex items-start gap-3 rounded-md border px-4 py-3 text-sm font-medium
            transition-all duration-300 ${notificationColors[notification.type]}`}
        >
          <span className="mt-0.5 text-base leading-none">
            {notificationIcons[notification.type]}
          </span>
          <span className="flex-1">{notification.message}</span>
          <button
            className="ml-2 opacity-60 hover:opacity-100"
            onClick={() => setNotification(null)}
          >
            ✕
          </button>
        </div>
      )}

      {stage === "published" ? (
        <div className="text-center py-8 space-y-2">
          <div className="text-5xl mb-3">🎉</div>
          <div className="text-emerald-700 font-semibold text-xl">
            Training Plan Approved!
          </div>
          <p className="text-muted-foreground text-sm">
            The plan has been saved to the database and is ready for LMS export.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Edit feedback box */}
          {showEditBox && (
            <div className="space-y-2">
              <label className="block text-sm font-medium">
                Your Feedback
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Describe what you'd like changed in the training plan…"
                className="w-full rounded-md border p-3 bg-background min-h-[120px] text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                autoFocus
              />
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-3 justify-center">
            {!showEditBox ? (
              <>
                <button
                  className="rounded-md bg-primary px-6 py-2.5 text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  onClick={handleApprove}
                  disabled={isProcessing}
                >
                  {isProcessing ? "Approving…" : "Approve"}
                </button>
                <button
                  className="rounded-md border-2 border-primary px-6 py-2.5 text-primary font-medium hover:bg-primary/10 disabled:opacity-50 transition-colors"
                  onClick={handleEdit}
                  disabled={isProcessing}
                >
                  Edit
                </button>
              </>
            ) : (
              <>
                <button
                  className="rounded-md bg-primary px-6 py-2.5 text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  onClick={handleRevise}
                  disabled={isProcessing}
                >
                  {isProcessing ? "Revising…" : "Submit Changes"}
                </button>
                <button
                  className="rounded-md border px-6 py-2.5 font-medium hover:bg-muted disabled:opacity-50 transition-colors"
                  onClick={() => { setShowEditBox(false); setNotes(""); }}
                  disabled={isProcessing}
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
