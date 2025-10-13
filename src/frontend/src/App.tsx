import React, { useState } from "react";
import { Send, Bell, X, Plus, TrendingUp, ExternalLink, Eye } from "lucide-react";

function App() {
  // Chat states
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      content: "Hi! I'm your AI Trend News assistant. What topics would you like to stay updated on?"
    }
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [topics, setTopics] = useState([]);

  // Subscription widget states
  const [subEmail, setSubEmail] = useState("");
  const [subTopics, setSubTopics] = useState([]);
  const [subCurrentTopic, setSubCurrentTopic] = useState("");
  const [subSubmitting, setSubSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  // News preview modal states
  const [newsModal, setNewsModal] = useState({
    isOpen: false,
    title: '',
    summary: '',
    link: '',
    topic: '',
    content: '',
    loading: false
  });

  // Chat handlers
  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");

    // Add user message
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();

      // Check if backend returned news items
      if (data.news && Array.isArray(data.news)) {
        data.news.forEach(item => {
          setMessages(prev => [
            ...prev,
            {
              type: 'bot',
              content: `${item.topic}\n${item.summary}`,
              newsData: {
                topic: item.topic,
                summary: item.summary,
                link: item.link,
                title: item.title || item.topic
              }
            }
          ]);
        });
      } else {
        // fallback to plain response
        setMessages(prev => [
          ...prev,
          { type: 'bot', content: data.response || "Sorry, couldn't process that." }
        ]);
      }

    } catch (error) {
      console.error('Chat API error:', error);
      setMessages(prev => [...prev, { type: 'bot', content: "Oops! Something went wrong." }]);
    } finally {
      setIsTyping(false);
    }
  };

  // Handle news link click to open preview modal
  const handleNewsClick = async (newsData) => {
    setNewsModal({
      isOpen: true,
      title: newsData.title,
      summary: newsData.summary,
      link: newsData.link,
      topic: newsData.topic,
      content: '',
      loading: true
    });

    try {
      // Fetch full article content from backend
      const response = await fetch('/api/news-content', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: newsData.link }),
      });

      if (response.ok) {
        const data = await response.json();
        setNewsModal(prev => ({
          ...prev,
          content: data.content || 'Content not available',
          loading: false
        }));
      } else {
        setNewsModal(prev => ({
          ...prev,
          content: 'Unable to load full content',
          loading: false
        }));
      }
    } catch (error) {
      console.error('Error fetching news content:', error);
      setNewsModal(prev => ({
        ...prev,
        content: 'Error loading content',
        loading: false
      }));
    }
  };

  const closeNewsModal = () => {
    setNewsModal({
      isOpen: false,
      title: '',
      summary: '',
      link: '',
      topic: '',
      content: '',
      loading: false
    });
  };

  const extractTopics = (message) => {
    const commonTopics = ['ai', 'technology', 'climate', 'finance', 'health', 'crypto', 'space', 'politics', 'science'];
    return commonTopics.filter(topic => message.toLowerCase().includes(topic));
  };

  // Subscription widget handlers
  const addSubTopic = () => {
    if (subCurrentTopic.trim() && !subTopics.includes(subCurrentTopic.trim())) {
      setSubTopics([...subTopics, subCurrentTopic.trim()]);
      setSubCurrentTopic("");
    }
  };

  const removeSubTopic = (topic) => {
    setSubTopics(subTopics.filter(t => t !== topic));
  };

  const handleSubscribe = async () => {
    if (!subEmail || subTopics.length === 0) return;

    setSubSubmitting(true);

    try {
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: subEmail,
          topics: subTopics,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      setNotification({
        type: 'success',
        message: data.message || `Successfully subscribed ${subEmail} to: ${subTopics.join(', ')}`
      });

      setIsSubscribed(true);
      setSubEmail("");
      setSubTopics([]);

    } catch (error) {
      console.error('Subscription API error:', error);

      setNotification({
        type: 'error',
        message: 'Failed to subscribe. Please try again or check if the backend is running.'
      });
    } finally {
      setSubSubmitting(false);

      setTimeout(() => {
        setNotification(null);
      }, 5000);
    }
  };

  const handleUnsubscribe = async () => {
    setSubSubmitting(true);

    try {
      const response = await fetch('/api/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: subEmail,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      setNotification({
        type: 'success',
        message: data.message || 'Successfully unsubscribed'
      });

      setIsSubscribed(false);

    } catch (error) {
      console.error('Unsubscribe API error:', error);

      setNotification({
        type: 'error',
        message: 'Failed to unsubscribe. Please try again.'
      });
    } finally {
      setSubSubmitting(false);

      setTimeout(() => {
        setNotification(null);
      }, 5000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Success/Error Notification */}
      {notification && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 px-6 py-3 rounded-lg shadow-lg border ${
          notification.type === 'success'
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              notification.type === 'success' ? 'bg-green-600' : 'bg-red-600'
            }`}></div>
            <p className="text-sm font-medium">{notification.message}</p>
            <button
              onClick={() => setNotification(null)}
              className="ml-2 text-gray-500 hover:text-gray-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* News Preview Modal */}
      {newsModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-gray-900 line-clamp-2">
                  {newsModal.title}
                </h2>
                <p className="text-sm text-blue-600 mt-1">#{newsModal.topic}</p>
              </div>
              <div className="flex items-center gap-2 ml-4">
                {/* Subscribe/Unsubscribe Toggle */}
                <button
                  onClick={isSubscribed ? handleUnsubscribe : () => {
                    if (!subTopics.includes(newsModal.topic)) {
                      setSubTopics(prev => [...prev, newsModal.topic]);
                    }
                  }}
                  disabled={subSubmitting}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors duration-200 ${
                    isSubscribed
                      ? 'bg-red-100 text-red-700 hover:bg-red-200'
                      : 'bg-green-100 text-green-700 hover:bg-green-200'
                  } disabled:opacity-50`}
                >
                  {subSubmitting ? '...' : (isSubscribed ? 'Unsubscribe' : 'Subscribe')}
                </button>
                <button
                  onClick={closeNewsModal}
                  className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-4 overflow-y-auto max-h-[70vh]">
              {/* Summary */}
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Summary</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{newsModal.summary}</p>
              </div>

              {/* Full Content */}
              <div className="mb-4">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Full Article</h3>
                {newsModal.loading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2 text-gray-500">Loading content...</span>
                  </div>
                ) : (
                  <div className="text-gray-600 text-sm leading-relaxed whitespace-pre-wrap">
                    {newsModal.content || 'Content preview not available'}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-gray-400" />
                <span className="text-xs text-gray-500">News Preview</span>
              </div>
              <a
                href={newsModal.link}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 text-sm"
              >
                <span>Read Full Article</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="flex items-center justify-center">
          <TrendingUp className="w-6 h-6 text-blue-600 mr-2" />
          <h1 className="text-xl font-semibold text-gray-900">AI Trend News</h1>
        </div>
      </div>

      {/* Subscription Widget - Top Right */}
      <div className="fixed top-20 right-4 md:right-6 bg-white rounded-lg shadow-lg border border-gray-200 p-4 w-72 md:w-80 z-40 max-h-96 overflow-y-auto">
        <h3 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
          <Bell className="w-4 h-4 text-blue-600" />
          Subscribe to Updates
        </h3>

        {/* Add Topics */}
        <div className="mb-3">
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={subCurrentTopic}
              onChange={(e) => setSubCurrentTopic(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSubTopic()}
              placeholder="Add topic..."
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={addSubTopic}
              disabled={!subCurrentTopic.trim()}
              className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          {/* Show topics */}
          {subTopics.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {subTopics.map((topic, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-md text-xs"
                >
                  {topic}
                  <button onClick={() => removeSubTopic(topic)}>
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Email Input */}
        <input
          type="email"
          value={subEmail}
          onChange={(e) => setSubEmail(e.target.value)}
          placeholder="your.email@example.com"
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {/* Subscribe Button */}
        <button
          onClick={handleSubscribe}
          disabled={subSubmitting || !subEmail || subTopics.length === 0}
          className="w-full bg-green-600 text-white py-2 rounded-md hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium text-sm transition-colors duration-200"
        >
          {subSubmitting ? "Processing..." : "Subscribe"}
        </button>

        {/* Subscription Status */}
        {isSubscribed && (
          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
            <p className="text-xs text-green-700">✓ You're subscribed to updates</p>
          </div>
        )}
      </div>

      {/* Main Chat Container */}
      <div className="flex-1 flex flex-col w-full max-w-4xl mx-auto px-4 md:px-6">
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4 min-h-0">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs sm:max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-3 rounded-2xl shadow-sm ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white rounded-br-md'
                    : 'bg-white border border-gray-200 text-gray-900 rounded-bl-md'
                }`}
              >
                <p className="text-sm leading-relaxed whitespace-pre-line">{message.content}</p>

                {/* News Preview Button */}
                {message.newsData && (
                  <button
                    onClick={() => handleNewsClick(message.newsData)}
                    className="mt-2 flex items-center gap-2 px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs hover:bg-blue-100 transition-colors duration-200"
                  >
                    <Eye className="w-3 h-3" />
                    <span>Preview News</span>
                  </button>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg px-4 py-2 max-w-xs">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          )}

          {/* Current Topics Display */}
          {topics.length > 0 && (
            <div className="flex justify-center">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800 mb-2">Your tracked topics:</p>
                <div className="flex flex-wrap gap-1">
                  {topics.map((topic, i) => (
                    <span key={i} className="bg-blue-600 text-white px-2 py-1 rounded-md text-xs">
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Chat Input */}
        <div className="border-t border-gray-200 bg-white p-4 flex-shrink-0">
          <div className="flex gap-2 max-w-4xl mx-auto">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Tell me what topics you want to follow..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping}
              className="px-6 py-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all duration-200 shadow-sm hover:shadow-md"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
