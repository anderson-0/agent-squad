/**
 * Dashboard Layout
 *
 * Main layout wrapper for authenticated dashboard pages
 * - Desktop: Persistent sidebar (240px) + Header + Main content
 * - Mobile: Header + Drawer sidebar + Main content
 */

import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { MobileNav } from '@/components/layout/MobileNav';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      {/* Desktop Sidebar */}
      <Sidebar />

      {/* Mobile Drawer */}
      <MobileNav />

      {/* Main Content Area */}
      <div className="flex flex-col md:pl-60">
        {/* Header */}
        <Header />

        {/* Page Content */}
        <main className="flex-1">
          <div className="px-4 py-6 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
