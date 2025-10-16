import { useState } from "react";
import { toast } from "sonner";

export interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  toolChain?: any[];
  timestamp: Date;
}

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuery, setCurrentQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedToolChainMessage, setSelectedToolChainMessage] = useState<Message | null>(null);

  const sendMessage = async () => {
    if (!currentQuery.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: currentQuery,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentQuery("");
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/respond', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: messages.length > 0 ? {...messages, userMessage} : userMessage.content
        }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const toolChain = data.reply || [];

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        content: `I've prepared a tool chain with ${toolChain.length} step(s) to answer your query.`,
        toolChain,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, agentMessage]);
      setSelectedToolChainMessage(agentMessage);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadJSON = (toolChain: any[]) => {
    const blob = new Blob([JSON.stringify(toolChain, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tool-chain-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = (toolChain: any[]) => {
    navigator.clipboard.writeText(JSON.stringify(toolChain, null, 2)).then(() => {
      toast.success("Tool chain copied to clipboard!");
    });
  };

  const clearChat = () => {
    setMessages([]);
    setSelectedToolChainMessage(null);
  };

  const sampleQueries = [
    "Summarize work items similar to don:core:dvrv-us-1:devo/0:issue/1",
    "Prioritize my P0 issues and add them to the current sprint",
    "Summarize high severity tickets from the customer UltimateCustomer",
    "What are my all issues in the triage stage under part FEAT-123?",
    "List all high severity tickets coming in from slack from customer Cust123 and generate a summary of them.",
    "Given a customer meeting transcript T, create action items and add them to my current sprint"
  ];

  return {
    messages,
    setMessages,
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
  };
};
