import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/authContext";
import { Toaster } from "sonner";
import { LanguageProvider } from "@/context/languageContext";
import { NetworkProvider } from "@/context/NetworkContext";
import { MultiWebSocketProvider } from "@/context/MultiWebSocketContext";
import { PluginProvider } from "@/context/PluginContext";
import { ModelProvider } from "@/context/ModelContext";
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SDN Launch Control",
  description: "SDN Launch Control",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <LanguageProvider>
          <NetworkProvider>
            <Toaster />
            <AuthProvider>
              <PluginProvider>
                <ModelProvider>
                  <MultiWebSocketProvider>{children}</MultiWebSocketProvider>
                </ModelProvider>
              </PluginProvider>
            </AuthProvider>
          </NetworkProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
