import React, { useState } from 'react';
import { Mail, Plus, X, TrendingUp, Bell } from 'lucide-react';

function App() {
  const [topics, setTopics] = useState<string[]>([]);
  const [currentTopic, setCurrentTopic] = useState('');
  const [email, setEmail] = useState('');
  const [emailOptIn, setEmailOptIn] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState('');

  const addTopic = () => {
    if (currentTopic.trim() && !topics.includes(currentTopic.trim())) {
      setTopics([...topics, currentTopic.trim()]);
      setCurrentTopic('');
    }
  };

  const removeTopic = (topicToRemove: string) => {
    setTopics(topics.filter(topic => topic !== topicToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (topics.length === 0) {
      setSubmitStatus('Please add at least one topic');
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus('');

    try {
      // API call to your Python backend
      const response = await fetch('/api/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topics,
          email: emailOptIn ? email : null,
          timestamp: new Date().toISOString()
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSubmitStatus('Successfully subscribed to trend updates!');
        setTopics([]);
        setEmail('');
        setEmailOptIn(false);
      } else {
        setSubmitStatus(data.detail || 'Failed to subscribe. Please try again.');
      }
    } catch (error) {
      setSubmitStatus('Error connecting to server. Please make sure the backend is running.');
      console.error('Subscription error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTopic();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <TrendingUp className="w-8 h-8 text-indigo-600 mr-2" />
            <h1 className="text-3xl font-bold text-gray-900">AI Trend News</h1>
          </div>
          <p className="text-gray-600">
            Stay updated on the topics that matter to you. Our AI analyzes news trends and delivers personalized insights.
          </p>
        </div>

        {/* Main Form */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <div>
            {/* Topic Input Section */}
            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                What topics interest you?
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={currentTopic}
                  onChange={(e) => setCurrentTopic(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="e.g., AI technology, climate change, cryptocurrency..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
                <button
                  type="button"
                  onClick={addTopic}
                  disabled={!currentTopic.trim()}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>

              {/* Topics Display */}
              {topics.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">Your topics:</p>
                  <div className="flex flex-wrap gap-2">
                    {topics.map((topic, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-1 bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm"
                      >
                        <span>{topic}</span>
                        <button
                          type="button"
                          onClick={() => removeTopic(topic)}
                          className="hover:bg-indigo-200 rounded-full p-1"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Email Notification Section */}
            <div className="mb-6">
              <div className="flex items-center gap-3 mb-3">
                <input
                  type="checkbox"
                  id="email-opt-in"
                  checked={emailOptIn}
                  onChange={(e) => setEmailOptIn(e.target.checked)}
                  className="w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                />
                <label htmlFor="email-opt-in" className="flex items-center text-sm font-medium text-gray-700 cursor-pointer">
                  <Bell className="w-4 h-4 mr-1" />
                  Get email notifications when you're away
                </label>
              </div>

              {emailOptIn && (
                <div className="ml-7">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@example.com"
                    required={emailOptIn}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    We'll send you trend updates when new information is available
                  </p>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting || topics.length === 0}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 text-white py-3 px-6 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Processing...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4" />
                  Start Getting Trend Updates
                </>
              )}
            </button>

            {/* Status Message */}
            {submitStatus && (
              <div className={`mt-4 p-3 rounded-lg text-sm ${
                submitStatus.includes('Successfully')
                  ? 'bg-green-100 text-green-800 border border-green-200'
                  : 'bg-red-100 text-red-800 border border-red-200'
              }`}>
                {submitStatus}
              </div>
            )}
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <TrendingUp className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
            <h3 className="font-semibold text-gray-900">AI-Powered Analysis</h3>
            <p className="text-sm text-gray-600">Smart algorithms analyze news trends in real-time</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <Bell className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
            <h3 className="font-semibold text-gray-900">Real-time Updates</h3>
            <p className="text-sm text-gray-600">Get notified as trends develop and change</p>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <Mail className="w-8 h-8 text-indigo-600 mx-auto mb-2" />
            <h3 className="font-semibold text-gray-900">Email Digest</h3>
            <p className="text-sm text-gray-600">Optional email summaries when you're away</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
