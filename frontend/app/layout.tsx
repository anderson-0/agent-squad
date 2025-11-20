import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from '@/components/ui/toaster';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Agent Squad - AI-Powered Software Development',
  description:
    'Build and manage AI agent squads for software development. Orchestrate intelligent agents, execute tasks, and monitor workflows in real-time with advanced collaboration tools.',
  keywords: [
    'AI agents',
    'multi-agent system',
    'software development',
    'task orchestration',
    'workflow automation',
    'agent collaboration',
    'LLM orchestration',
    'intelligent agents',
  ],
  authors: [{ name: 'Agent Squad Team' }],
  creator: 'Agent Squad',
  publisher: 'Agent Squad',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'),
  openGraph: {
    title: 'Agent Squad - AI-Powered Software Development',
    description:
      'Build and manage AI agent squads for software development. Orchestrate intelligent agents, execute tasks, and monitor workflows in real-time.',
    url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    siteName: 'Agent Squad',
    locale: 'en_US',
    type: 'website',
    images: [
      {
        url: '/og-image.png', // Add this image later
        width: 1200,
        height: 630,
        alt: 'Agent Squad - AI-Powered Software Development',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Agent Squad - AI-Powered Software Development',
    description:
      'Build and manage AI agent squads for software development. Orchestrate intelligent agents and monitor workflows.',
    images: ['/twitter-image.png'], // Add this image later
    creator: '@agentsquad',
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    // Add these when available
    // google: 'your-google-verification-code',
    // yandex: 'your-yandex-verification-code',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
