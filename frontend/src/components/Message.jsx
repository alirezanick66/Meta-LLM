import React from "react"

/**
 * کامپوننت نمایش یک پیام
 * @param {Object} message - شیء پیام {role: 'user'|'assistant', content: string, timestamp: Date}
 */
const Message = ({ message }) => {
	const isUser = message.role === "user"

	return (
		<div
			className={`flex w-full mb-4 ${isUser ? "justify-start" : "justify-end"}`}
		>
			<div
				className={`max-w-[80%] md:max-w-[70%] rounded-2xl px-4 py-3 ${
					isUser
						? "bg-user-bg text-white"
						: "bg-bot-bg text-gray-100 border border-gray-700"
				}`}
			>
				{/* محتوای پیام */}
				<div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
					{message.content}
				</div>

				{/* زمان */}
				{message.timestamp && (
					<div className="text-xs text-gray-500 mt-2 text-left">
						{new Date(message.timestamp).toLocaleTimeString(
							"fa-IR",
							{
								hour: "2-digit",
								minute: "2-digit",
							},
						)}
					</div>
				)}
			</div>
		</div>
	)
}

export default Message
