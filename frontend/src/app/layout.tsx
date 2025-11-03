import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SmartPDF Shrinker',
  description: 'Intelligent PDF compression platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-white min-h-screen">
        <main className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-10 px-6 py-12">
          <header className="space-y-2 text-center">
            <h1 className="text-4xl font-bold">SmartPDF Shrinker</h1>
            <p className="text-slate-300">
              Upload your PDF, choose a target size, and let the AI-powered compressor do the rest.
            </p>
          </header>
          {children}
        </main>
      </body>
    </html>
  )
}
