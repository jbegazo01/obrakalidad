"use client";

import { useState } from "react";
import { useAppData } from "@/lib/app-data-context";
import { ProtocoloCard } from "@/components/protocolo-card";
import { NewProtocoloDialog } from "@/components/new-protocolo-dialog";
import { GestorEtapas } from "@/components/configuracion/GestorEtapas";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function CriteriosInspeccionPage() {
  const { protocolos, etapasConstructivas } = useAppData();
  const [activeTab, setActiveTab] = useState("etapas");

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList>
        <TabsTrigger value="etapas">Etapas Constructivas</TabsTrigger>
        <TabsTrigger value="protocolos">Protocolos por Etapa</TabsTrigger>
      </TabsList>

      <TabsContent value="etapas" className="space-y-4">
        <GestorEtapas />
      </TabsContent>

      <TabsContent value="protocolos" className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Haz clic en una etapa para ver sus protocolos.
          </p>
          <NewProtocoloDialog />
        </div>

        {etapasConstructivas.length === 0 ? (
          <div className="rounded-lg border border-dashed p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Crea una etapa primero en la pestaña "Etapas Constructivas"
            </p>
          </div>
        ) : (
          <div className="border rounded-lg divide-y">
            {etapasConstructivas.map((etapa) => {
              const protocolosDeEtapa = protocolos.filter((p) => p.etapaId === etapa.id);
              return (
                <details key={etapa.id} className="group">
                  <summary className="cursor-pointer select-none p-4 hover:bg-muted/50 transition flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold">{etapa.nombre}</h3>
                      {etapa.descripcion && (
                        <p className="text-xs text-muted-foreground mt-1">{etapa.descripcion}</p>
                      )}
                    </div>
                    <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded ml-2">
                      {protocolosDeEtapa.length}
                    </span>
                  </summary>
                  <div className="p-4 bg-muted/30 border-t">
                    {protocolosDeEtapa.length === 0 ? (
                      <p className="text-xs text-muted-foreground italic">Sin protocolos definidos</p>
                    ) : (
                      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                        {protocolosDeEtapa.map((p) => (
                          <ProtocoloCard key={p.id} protocolo={p} />
                        ))}
                      </div>
                    )}
                  </div>
                </details>
              );
            })}
          </div>
        )}
      </TabsContent>
    </Tabs>
  );
}
