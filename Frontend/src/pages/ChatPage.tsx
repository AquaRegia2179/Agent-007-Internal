import { useRef, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import { Toaster } from "sonner";
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import { useChat } from '../hooks/useChat';

export default function ChatPage() {
  const navigate = useNavigate();
  const {
    messages,
    currentQuery,
    setCurrentQuery,
    isLoading,
    selectedToolChainMessage,
    setSelectedToolChainMessage,
    sendMessage,
    downloadJSON,
    copyToClipboard,
    clearChat,
    sampleQueries,
  } = useChat();
  const chatRef = useRef<HTMLDivElement>(null);

  const handleScrollToBottom = () => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  };
  useEffect(() => {
    handleScrollToBottom();
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white">
      <Navbar onClearChat={clearChat} />

      <div className="container p-6">
        <button
          onClick={() => navigate('/')}
          className="mb-4 bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          ← Back to Home
        </button>

        {/* Main Content - Side by Side */}
        <div className="flex gap-6 mb-6">
          {/* Chat History */}
          <div className="flex-1 bg-gray-800 rounded-lg shadow-2xl p-6 max-w-[calc(50vw-1.5rem)]">
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">Chat History</h2>
            <div className="h-96 px-2 my-4 overflow-y-auto chat-history" ref={chatRef}>
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-center">
                  <div>
                    <h3 className="text-xl font-semibold text-yellow-400 mb-2">Welcome to AI Agent 007</h3>
                    <p className="text-gray-400">Start a conversation by typing a query below. I'll use the best tools to answer your questions.</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-2xl px-4 py-2 rounded-lg ${message.type === 'user'
                        ? 'bg-yellow-500 text-black'
                        : 'bg-gray-700 text-white'
                        }`}>
                        <p className="text-sm">{message.content}</p>
                        {message.type === 'agent' && message.toolChain && message.toolChain.length > 0 && (
                          <button
                            onClick={() => setSelectedToolChainMessage(message)}
                            className="mt-2 text-xs text-yellow-300 hover:text-yellow-100 underline"
                          >
                            View Tool Chain ({message.toolChain.length} steps)
                          </button>
                        )}
                        <p className="text-xs opacity-70 mt-2">
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-700 text-white px-4 py-2 rounded-lg">
                        <div className="flex items-center gap-2">
                          <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                          <span>Analyzing query and preparing tools...</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
            {/* Input Section */}
            <div className="bg-gray-800 rounded-lg shadow-2xl">
              <div className="flex gap-3 mb-4">
                <input
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Ask me anything... (e.g., 'Summarize my P0 issues')"
                  className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:ring-2 focus:ring-yellow-400 focus:border-transparent text-white placeholder-gray-400"
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!currentQuery.trim() || isLoading}
                  className="bg-yellow-500 hover:bg-yellow-400 text-black px-6 py-3 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Send
                </button>
                <button
                  onClick={clearChat}
                  className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-3 rounded-lg font-medium transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
          {/* Tool Chain Display */}
          <div className="flex-1 bg-gray-800 rounded-lg shadow-2xl p-6 max-w-[calc(50vw-1.5rem)]">
            <h2 className="text-xl font-semibold text-yellow-400 mb-4">Tool Chain</h2>
            <div className="h-full overflow-auto">
              {selectedToolChainMessage ? (
                <div className="bg-gray-700 rounded-lg p-4">
                  {/* <h4 className="font-semibold text-yellow-400 mb-2">Query: {selectedToolChainMessage.content}</h4> */}
                  <pre className="bg-gray-900 border border-gray-600 rounded-lg p-4 text-sm overflow-auto h-96 font-mono">
                    <code className="text-green-400">{JSON.stringify(selectedToolChainMessage.toolChain, null, 2)}</code>
                  </pre>
                  <div className="flex gap-2 mt-4">
                    <button
                      onClick={() => copyToClipboard(selectedToolChainMessage.toolChain!)}
                      className="text-sm bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded transition-colors"
                    >
                      Copy JSON
                    </button>
                    <button
                      onClick={() => downloadJSON(selectedToolChainMessage.toolChain!)}
                      className="text-sm bg-yellow-500 hover:bg-yellow-400 text-black px-4 py-2 rounded transition-colors"
                    >
                      Download
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-center">
                  <div>
                    <p className="text-gray-400">Ask any query to display the JSON response here.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        {/* Sample Queries */}
        <div>
          <h3 className="text-sm font-semibold text-yellow-400 mb-2">Try these sample queries:</h3>
          <div className="flex flex-wrap gap-2">
            {sampleQueries.map((sample, index) => (
              <button
                key={index}
                onClick={() => setCurrentQuery(sample)}
                className="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded-lg transition-colors text-left"
                disabled={isLoading}
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Footer />
      <Toaster theme="dark" />
    </div>
  );
}
