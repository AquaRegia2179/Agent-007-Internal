export default function Footer() {
  return (
    <footer className="bg-gray-900 border-t border-gray-700 mt-12 px-6 py-8">
      <div className="container mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center gap-3 mb-4 md:mb-0">
            <img src="/Logo.png" alt="AI Agent 007 Logo" className="w-8 h-8" />
            <span className="text-white font-medium">AI Agent 007</span>
          </div>
          <div className="text-gray-400 text-sm text-center md:text-right">
            <p>&copy; {new Date().getFullYear()} AI Agent 007. Bridging developers and customers with intelligent automation.</p>
            <p className="mt-1">Built with advanced AI and tool integration capabilities.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
