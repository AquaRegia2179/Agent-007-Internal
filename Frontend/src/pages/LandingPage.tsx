import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function LandingPage() {

  const features = [
    {
      title: "Intelligent Tool Selection",
      description: "Automatically selects and sequences the right tools for your domain-specific queries.",
      icon: "🛠️"
    },
    {
      title: "Conversational Interface",
      description: "Natural language interaction with context-aware responses and tool chain visualization.",
      icon: "💬"
    },
    {
      title: "JSON Tool Chains",
      description: "View, copy, and download structured tool chains for integration and analysis.",
      icon: "📋"
    },
    {
      title: "Real-time Processing",
      description: "Fast, efficient processing with live updates and error handling.",
      icon: "⚡"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white">
      <Navbar onClearChat={()=>{/*Do Nothing -- No chat on Landing page*/}} />

      {/* Hero Section */}
      <div className="container mx-auto px-6 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-yellow-400 mb-6">
            AI Agent 007
          </h1>
          <p className="text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Your intelligent tool-using assistant for domain-specific question answering
          </p>
          <Link
            to="/chat"
            className="bg-yellow-500 hover:bg-yellow-400 text-black px-8 py-4 rounded-lg font-bold text-lg transition-colors inline-block text-center"
          >
            Start Conversation
          </Link>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          {features.map((feature, index) => (
            <div key={index} className="bg-gray-800 rounded-lg p-6 text-center">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-yellow-400 mb-2">{feature.title}</h3>
              <p className="text-gray-300">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      <Footer />
    </div>
  );
}
