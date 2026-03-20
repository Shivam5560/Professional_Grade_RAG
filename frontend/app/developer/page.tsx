'use client';

import { useEffect, useState } from 'react';
import { Header } from '@/components/layout/Header';
import { GlassmorphismPortfolioBlock } from '@/components/ui/glassmorphism-portfolio-block-shadcnui';
import { ShaderAnimation } from '@/components/ui/shader-animation';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function DeveloperPage() {
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-45">
        <ShaderAnimation className="w-full h-full" speed={0.08} />
      </div>

      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.18),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[12%] left-[-12%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl float-slower" />
      <div className="pointer-events-none absolute bottom-[-18%] right-[8%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-4)/0.16),transparent_70%)] blur-3xl float-slowest" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-12">
        <div className="max-w-6xl mx-auto">
          <GlassmorphismPortfolioBlock profileImageSrc="/images/developer/profile-main.png" />
        </div>
      </main>
    </div>
  );
}
