import clsx from "clsx";
import { AlertTriangle, AlertCircle, Info } from "lucide-react";

const config = {
  Low: { color: "text-teal", bg: "bg-teal/10", border: "border-teal/30", Icon: Info },
  Medium: { color: "text-periwinkle", bg: "bg-periwinkle/10", border: "border-periwinkle/30", Icon: AlertCircle },
  High: { color: "text-coral", bg: "bg-coral/10", border: "border-coral/30", Icon: AlertTriangle },
};

export default function UrgencyBadge({ level }: { level: "Low" | "Medium" | "High" }) {
  const { color, bg, border, Icon } = config[level] || config.Medium;
  return (
    <span className={clsx("inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-display font-medium border", color, bg, border)}>
      <Icon size={14} />
      {level} urgency
    </span>
  );
}
