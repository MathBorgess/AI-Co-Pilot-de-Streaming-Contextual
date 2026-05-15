import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Co-Pilot Streaming Contextual',
  description: 'Real-time AI streaming copilot with RAG and agents',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="app-body">
        {children}
      </body>
    </html>
  );
}
