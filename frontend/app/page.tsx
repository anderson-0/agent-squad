'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store/auth';

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuthStore();

  useEffect(() => {
    // Redirect authenticated users to dashboard
    if (!isLoading && user) {
      router.push('/squads');
    }
  }, [user, isLoading, router]);

  // Show landing page for unauthenticated users
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8 md:p-24">
      <main className="flex flex-col items-center gap-8">
        <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent text-center">
          Agent Squad
        </h1>
        <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 text-center max-w-2xl">
          AI-Powered Software Development SaaS Platform
        </p>
        <div className="flex flex-col sm:flex-row gap-4 mt-8">
          <Link
            href="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center font-medium"
          >
            Get Started
          </a>
          <a
            href="/dashboard"
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            View Dashboard
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 border border-gray-300 rounded-lg hover:border-gray-400 transition-colors"
          </Link>
          <Link
            href="/register"
            className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:border-gray-400 dark:hover:border-gray-500 transition-colors text-center font-medium"
          >
            Create Account
          </Link>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-4xl w-full">
          <div className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h3 className="text-lg font-semibold mb-2">Customizable Squads</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Build your perfect AI team with 2-10 specialized agents
            </p>
          </div>
          <div className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h3 className="text-lg font-semibold mb-2">Multi-Project Support</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Connect to Git repos and ticket systems seamlessly
            </p>
          </div>
          <div className="p-6 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
            <h3 className="text-lg font-semibold mb-2">Real-time Dashboard</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Monitor agent collaboration and task progress live
            </p>
          </div>
        </div>
        <div className="mt-8 text-sm text-gray-500 dark:text-gray-400">
          Already have an account?{' '}
          <Link href="/login" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign in
          </Link>
        </div>
      </main>
    </div>
  );
}
