import React from "react"
import MessageActions from "./MessageActions"
import { useTypingEffect } from "../hooks/useTypingEffect"

/**
 * کامپوننت نمایش پیام (با typing effect)
 * @param {Object} message - شیء پیام
 * @param {Function} onRegenerate - تابع تولید مجدد
 * @param {boolean} enableTyping - فعال بودن افکت تایپ
 */
const Message = ({ message, onRegenerate, enableTyping = false }) => {
	const isUser = message.role === "user"

	// فقط برای پیام‌های ربات typing effect فعال میشه
	const { displayedText, isTyping } = useTypingEffect(
		message.content,
		20,
		enableTyping && !isUser,
	)

	const content = enableTyping && !isUser ? displayedText : message.content

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
					{content}
					{/* Cursor animation وقتی در حال تایپه */}
					{isTyping && (
						<span className="inline-block w-0.5 h-4 bg-gray-800 ml-1 animate-pulse">
							▌
						</span>
					)}
				</div>

				{/* Actions - فقط وقتی typing تموم شده */}
				{!isTyping && (
					<MessageActions
						content={message.content}
						onRegenerate={!isUser ? onRegenerate : null}
						isUser={isUser}
					/>
				)}
			</div>
		</div>
	)
}

export default Message
