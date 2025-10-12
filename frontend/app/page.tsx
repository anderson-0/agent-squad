export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <main className="flex flex-col items-center gap-8">
        <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Agent Squad
        </h1>
        <p className="text-xl text-gray-600 text-center max-w-2xl">
          AI-Powered Software Development SaaS Platform
        </p>
        <div className="flex gap-4 mt-8">
          <a
            href="/docs"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Get Started
          </a>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 border border-gray-300 rounded-lg hover:border-gray-400 transition-colors"
          >
            API Documentation
          </a>
        </div>
        <div className="grid grid-cols-3 gap-8 mt-16 max-w-4xl">
          <div className="p-6 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Customizable Squads</h3>
            <p className="text-gray-600 text-sm">
              Build your perfect AI team with 2-10 specialized agents
            </p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Multi-Project Support</h3>
            <p className="text-gray-600 text-sm">
              Connect to Git repos and ticket systems seamlessly
            </p>
          </div>
          <div className="p-6 border border-gray-200 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Real-time Dashboard</h3>
            <p className="text-gray-600 text-sm">
              Monitor agent collaboration and task progress live
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
