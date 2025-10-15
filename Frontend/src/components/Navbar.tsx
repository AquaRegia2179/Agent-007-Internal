import { useState } from 'react';
import { Link } from 'react-router-dom';

interface NavbarProps {
  onClearChat: () => void;
}

export default function Navbar({ onClearChat }: NavbarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className="bg-gray-900 border-b border-gray-700 px-6 py-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link to="/chat" className="flex items-center gap-3">
          <img src="/Logo.png" alt="AI Agent 007 Logo" className="w-10 h-10" />
          <h1 className="text-2xl font-bold text-yellow-400">
            AI Agent 007
          </h1>
        </Link>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-6">
          <a href="#" className="text-gray-300 hover:text-white transition-colors">Features</a>
          <a href="#" className="text-gray-300 hover:text-white transition-colors">Documentation</a>
          <a href="#" className="text-gray-300 hover:text-white transition-colors">Support</a>
          <button
            onClick={onClearChat}
            className="bg-yellow-500 hover:bg-yellow-400 text-black px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Clear Chat
          </button>
        </div>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="md:hidden text-white"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden mt-4 pb-4 border-t border-gray-700">
          <div className="flex flex-col gap-4 pt-4">
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Features</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Documentation</a>
            <a href="#" className="text-gray-300 hover:text-white transition-colors">Support</a>
            <button
              onClick={onClearChat}
              className="bg-yellow-500 hover:bg-yellow-400 text-black px-4 py-2 rounded-lg font-medium transition-colors w-fit"
            >
              Clear Chat
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
