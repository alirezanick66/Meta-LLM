import React from "react"
import MessageActions from "./MessageActions"

/**
 * کامپوننت نمایش پیام (با actions)
 * @param {Object} message - شیء پیام
 * @param {Function} onRegenerate - تابع تولید مجدد پاسخ
 */
const Message = ({ message, onRegenerate }) => {
	const isUser = message.role === "user"

	return (
		<div className="w-full py-2 animate-fadeIn group">
			<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
				{/* متن پیام */}
				<div
					className={`text-sm md:text-base leading-7 whitespace-pre-wrap break-words 
						transition-all duration-300 px-4 py-3 rounded-2xl 
						w-fit max-w-[85%]
						${isUser ? "bg-[#fff6d9] text-gray-800" : "text-gray-800"}`}
				>
					{message.content}
				</div>

				{/* Actions - فقط با hover نمایش داده میشه */}
				<MessageActions
					content={message.content}
					onRegenerate={!isUser ? onRegenerate : null}
					isUser={isUser}
				/>
			</div>
		</div>
	)
}

export default Message
