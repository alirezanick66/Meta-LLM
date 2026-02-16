import React, { useMemo } from "react"
import MessageActions from "./MessageActions"
import { useTypingEffect } from "../hooks/useTypingEffect"

/**
 * کامپوننت نمایش پیام (نسخه بهبود یافته)
 *
 * بهبودها:
 * - useMemo برای جلوگیری از re-render غیرضروری
 * - مدیریت بهتر حالت typing
 *
 * @param {Object} message - شیء پیام
 * @param {Function} onRegenerate - تابع تولید مجدد
 * @param {boolean} isRegenerating - آیا در حال regenerate است؟
 * @param {boolean} enableTyping - فعال بودن افکت تایپ
 * @param {string} typingEffect - نوع افکت: 'slideIn' | 'default'
 */
const Message = ({
	message,
	onRegenerate,
	isRegenerating = false,
	enableTyping = false,
	typingEffect = "slideIn",
}) => {
	const isUser = message.role === "user"

	// Typing effect (فقط برای assistant و فقط وقتی enabled باشه)
	const { displayedText, isTyping } = useTypingEffect(
		message.content,
		20, // سرعت
		enableTyping && !isUser,
	)

	// انتخاب محتوای نمایشی (با useMemo برای بهینه‌سازی)
	const content = useMemo(() => {
		return enableTyping && !isUser ? displayedText : message.content
	}, [enableTyping, isUser, displayedText, message.content])

	// Render محتوا با افکت
	const renderContent = useMemo(() => {
		if (!enableTyping || isUser) {
			return content
		}

		switch (typingEffect) {
			case "slideIn":
				// کل متن لغزش از راست
				return (
					<span className="inline-block animate-slideInRight">
						{content}
					</span>
				)

			default:
				// حالت عادی (typewriter)
				return content
		}
	}, [enableTyping, isUser, content, typingEffect])

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
					{renderContent}

					{/* Cursor animation (فقط برای حالت default) */}
					{isTyping && typingEffect === "default" && (
						<span className="inline-block w-0.5 h-4 bg-gray-800 ml-1 animate-pulse">
							▌
						</span>
					)}
				</div>

				{/* Actions (فقط وقتی typing تموم شده) */}
				{!isTyping && (
					<MessageActions
						content={message.content}
						onRegenerate={!isUser ? onRegenerate : null}
						isUser={isUser}
						isRegenerating={isRegenerating}
					/>
				)}
			</div>
		</div>
	)
}

export default React.memo(Message) // ✅ Memoization برای جلوگیری از re-render
