import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface InspectionKpiCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  tone: "success" | "warning" | "error" | "info";
  trend?: { value: string; direction: "up" | "down" | "neutral" };
}

const toneStyles = {
  success: "text-emerald-600 bg-emerald-50 border-emerald-200",
  warning: "text-amber-600 bg-amber-50 border-amber-200",
  error: "text-red-600 bg-red-50 border-red-200",
  info: "text-blue-600 bg-blue-50 border-blue-200",
};

export function InspectionKpiCard({
  label,
  value,
  subtitle,
  icon: Icon,
  tone,
  trend,
}: InspectionKpiCardProps) {
  return (
    <Card className="border-l-4 border-l-transparent transition-shadow hover:shadow-md">
      <CardContent className="pt-6">
        <div className="flex items-start gap-4">
          <div className={`flex h-12 w-12 items-center justify-center rounded-xl border ${toneStyles[tone]}`}>
            <Icon className="h-6 w-6" />
          </div>
          <div className="flex-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {label}
            </p>
            <div className="mt-2 flex items-end gap-2">
              <p className="text-3xl font-bold tracking-tight">{value}</p>
              {trend && (
                <span
                  className={`text-xs font-semibold ${
                    trend.direction === "up"
                      ? "text-emerald-600"
                      : trend.direction === "down"
                        ? "text-red-600"
                        : "text-muted-foreground"
                  }`}
                >
                  {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "•"} {trend.value}
                </span>
              )}
            </div>
            {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
