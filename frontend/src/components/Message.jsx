import React from "react"

/**
 * کامپوننت نمایش پیام (کادر زرد به اندازه متن)
 * @param {Object} message - شیء پیام {role: 'user'|'assistant', content: string}
 */
const Message = ({ message }) => {
	const isUser = message.role === "user"

	return (
		<div className="w-full py-2 animate-fadeIn">
			{/* کانتینر اصلی */}
			<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
				{/* متن پیام - w-fit برای عرض دینامیک */}
				<div
					className={`text-sm md:text-base leading-7 whitespace-pre-wrap break-words 
						transition-all duration-300 px-4 py-3 rounded-2xl 
						w-fit max-w-[85%]
						${isUser ? "bg-[#fff6d9] text-gray-800" : "text-gray-800"}`}
				>
					{message.content}
				</div>
			</div>
		</div>
	)
}

export default Message
