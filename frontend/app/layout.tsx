import type { Metadata } from 'next'
import { Space_Grotesk, IBM_Plex_Mono } from 'next/font/google'
import './globals.css'
import { ClientProviders } from '@/components/layout/ClientProviders'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-geist-sans',
  display: 'swap',
})

const plexMono = IBM_Plex_Mono({
  subsets: ['latin'],
  variable: '--font-geist-mono',
  weight: ['400', '600'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'NexusMind Studio',
  description: 'Advanced RAG system with hybrid search and confidence scoring',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${plexMono.variable} theme-nexus dark`}
      data-theme-palette="nexus"
      data-theme-mode="dark"
    >
      <body>
        {children}
        <ClientProviders />
      </body>
    </html>
  )
}
