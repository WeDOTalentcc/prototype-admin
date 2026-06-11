import type { Metadata } from "next";
import { Inter, Open_Sans, Source_Serif_4 } from "next/font/google";
import "./globals.css";
import { EnvironmentBadge } from "@/components/layout/EnvironmentBadge";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
});

const openSans = Open_Sans({
  subsets: ["latin"],
  variable: "--font-open-sans",
  display: "swap"
});

const sourceSerif4 = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif-4",
  display: "swap"
});

export const metadata: Metadata = {
  metadataBase: new URL('https://app.wedotalent.com'),
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html suppressHydrationWarning>
      <head suppressHydrationWarning>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
      </head>
      <body
        className={`${inter.variable} ${openSans.variable} ${sourceSerif4.variable} antialiased bg-white`}
        suppressHydrationWarning
      >
        <EnvironmentBadge />
        {children}
      </body>
    </html>
  );
}
