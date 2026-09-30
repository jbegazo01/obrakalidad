import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/app-shell";
import { Toaster } from "@/components/ui/sonner";
import { AppDataProvider } from "@/lib/app-data-context";
import { AuthProvider } from "@/lib/auth-context";
import { ProjectSelectionProvider } from "@/lib/project-selection-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ObraCalidad | Gestión de Calidad en Obra",
  description: "Plataforma de gestión de calidad para empresas constructoras",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="es"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AppDataProvider>
          <AuthProvider>
            <ProjectSelectionProvider>
              <AppShell>{children}</AppShell>
              <Toaster />
            </ProjectSelectionProvider>
          </AuthProvider>
        </AppDataProvider>
      </body>
    </html>
  );
}
