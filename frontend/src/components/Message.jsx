import React from 'react';

/**
 * کامپوننت نمایش یک پیام
 * @param {Object} message - شیء پیام {role: 'user'|'assistant', content: string, timestamp: Date}
 */
const Message = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div
      className={`flex w-full mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[80%] md:max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-user-bg text-white'
            : 'bg-bot-bg text-gray-100 border border-gray-700'
        }`}
      >
        {/* Avatar و نام */}
        <div className="flex items-center gap-2 mb-2">
          <span className="text-lg">
            {isUser ? '👤' : '🤖'}
          </span>
          <span className="text-xs font-semibold text-gray-400">
            {isUser ? 'شما' : 'Meta'}
          </span>
        </div>

        {/* محتوای پیام */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
        </div>

        {/* منابع (اگر وجود داشته باشد) */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-700">
            <p className="text-xs text-gray-400 mb-2">📚 منابع:</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, idx) => (
                <span
                  key={idx}
                  className="text-xs bg-primary-secondary px-2 py-1 rounded"
                  title={source.hierarchy}
                >
                  [{source.index}] {source.source}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* زمان */}
        {message.timestamp && (
          <div className="text-xs text-gray-500 mt-2 text-left">
            {new Date(message.timestamp).toLocaleTimeString('fa-IR', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;