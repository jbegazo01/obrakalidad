import Link from "next/link";
import { Plus, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface InspectionSectionHeaderProps {
  title: string;
  subtitle: string;
  activeCount: number;
  onDateRangeChange?: (range: string) => void;
  dateRange?: string;
}

export function InspectionSectionHeader({
  title,
  subtitle,
  activeCount,
  onDateRangeChange,
  dateRange = "30days",
}: InspectionSectionHeaderProps) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
            <Badge
              variant="secondary"
              className="bg-blue-100 text-blue-700 hover:bg-blue-100"
            >
              {activeCount} Activas
            </Badge>
          </div>
          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{subtitle}</p>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Select value={dateRange} onValueChange={onDateRangeChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7days">Últimos 7 días</SelectItem>
              <SelectItem value="30days">Últimos 30 días</SelectItem>
              <SelectItem value="90days">Últimos 90 días</SelectItem>
              <SelectItem value="all">Todo el tiempo</SelectItem>
            </SelectContent>
          </Select>

          <Link href="/inspecciones/nueva">
            <Button size="sm" className="gap-2">
              <Plus className="h-4 w-4" />
              Nueva Inspección
            </Button>
          </Link>

          <Button variant="outline" size="sm" className="gap-2">
            <Download className="h-4 w-4" />
            Exportar
          </Button>
        </div>
      </div>
    </div>
  );
}
