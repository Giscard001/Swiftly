import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "FilesConvert — Conversion de fichiers tout-en-un",
  description:
    "Convertissez vos documents, images, audio, vidéo, archives et données en privé. Rapide, sans inscription, fichiers supprimés après 1h.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" suppressHydrationWarning className={inter.variable}>
      <body className={`${inter.className} min-h-screen bg-gray-50 text-gray-900 antialiased dark:bg-[#0a0e1a] dark:text-gray-100`}>
        <Providers>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
