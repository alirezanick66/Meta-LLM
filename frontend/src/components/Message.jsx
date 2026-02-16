import React from "react"

/**
 * کامپوننت نمایش پیام (بدون آواتار، چسبیده به راست)
 * @param {Object} message - شیء پیام {role: 'user'|'assistant', content: string, timestamp: Date}
 */
const Message = ({ message }) => {
	const isUser = message.role === "user"

	return (
		<div className="w-full py-6">
			{/* کانتینر محتوا: با ml-auto به سمت راست هل داده شده است */}
			<div className="max-w-3xl ml-auto mr-4 px-4">
				{/* متن پیام */}
				<div
					className={`text-sm md:text-base leading-7 whitespace-pre-wrap break-words text-gray-800
            ${isUser ? "bg-[#fff6d9] px-4 py-3 rounded-lg shadow-sm" : ""}`}
				>
					{message.content}
				</div>

				{/* زمان */}
				{message.timestamp && (
					<div className="text-xs text-gray-400 mt-1 mr-1">
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
