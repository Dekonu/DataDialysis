import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navigation } from '@/components/dashboard/navigation';
import { ThemeProvider } from '@/components/theme-provider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Data-Dialysis Dashboard',
  description: 'Health monitoring dashboard for Data-Dialysis pipeline',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className} suppressHydrationWarning>
        <ThemeProvider>
          <div className="min-h-screen bg-background transition-colors">
            <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
              <div className="container mx-auto px-4 py-4">
                <div className="flex items-center justify-between">
                  <h1 className="text-xl sm:text-2xl font-bold">Data-Dialysis Dashboard</h1>
                  <Navigation />
                </div>
              </div>
            </nav>
            <main className="container mx-auto px-4 py-4 sm:py-8 animate-fade-in">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
