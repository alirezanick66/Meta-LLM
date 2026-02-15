import React, { useState, useRef, useEffect } from 'react';

/**
 * کامپوننت ورودی پیام
 * @param {Function} onSend - تابعی که با فشردن ارسال صدا زده می‌شود
 * @param {boolean} isLoading - آیا در حال ارسال است؟
 */
const InputBox = ({ onSend, isLoading }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;

    onSend(trimmed);
    setMessage('');
    
    // Reset height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    // Enter برای ارسال، Shift+Enter برای خط جدید
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-gray-700 bg-primary-secondary p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="flex items-end gap-2">
          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="پیام خود را بنویسید..."
            disabled={isLoading}
            rows={1}
            className="flex-1 bg-primary-bg border border-gray-700 rounded-xl px-4 py-3 
                     text-white placeholder-gray-500 resize-none focus:outline-none 
                     focus:ring-2 focus:ring-primary-accent max-h-[200px] overflow-y-auto
                     scrollbar-thin disabled:opacity-50 disabled:cursor-not-allowed"
          />

          {/* دکمه ارسال */}
          <button
            type="submit"
            disabled={!message.trim() || isLoading}
            className="bg-primary-accent hover:bg-green-600 disabled:bg-gray-600 
                     disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 
                     transition-colors flex-shrink-0 font-semibold"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </span>
            ) : (
              '➤'
            )}
          </button>
        </div>

        {/* Character counter */}
        <div className="text-xs text-gray-500 mt-2 text-left">
          {message.length}/1000
        </div>
      </form>
    </div>
  );
};

export default InputBox;