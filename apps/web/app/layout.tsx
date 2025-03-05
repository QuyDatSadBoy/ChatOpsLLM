import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ChatOpsLLM',
  description: 'Production LLMOps chat platform by Trần Quý Đạt',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen bg-slate-50 antialiased">{children}</body>
    </html>
  );
}
