import React, { useState } from "react"

/**
 * دکمه‌های عملیات پیام (کپی، ریجنریت)
 */
const MessageActions = ({ content, onRegenerate, isUser }) => {
	const [copied, setCopied] = useState(false)

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(content)
			setCopied(true)
			setTimeout(() => setCopied(false), 2000)
		} catch (err) {
			console.error("Failed to copy:", err)
		}
	}

	return (
		<div
			className="opacity-0 group-hover:opacity-100 transition-opacity 
			flex gap-1 mt-2"
		>
			{/* دکمه کپی */}
			<button
				onClick={handleCopy}
				className="p-1.5 hover:bg-gray-100 rounded transition-colors text-xs flex items-center gap-1"
				title="کپی"
			>
				{copied ? (
					<>
						<span>✓</span>
						<span className="text-gray-600">کپی شد</span>
					</>
				) : (
					<>
						<span>📋</span>
						<span className="text-gray-600">کپی</span>
					</>
				)}
			</button>

			{/* دکمه ریجنریت (فقط برای پیام ربات) */}
			{!isUser && onRegenerate && (
				<button
					onClick={onRegenerate}
					className="p-1.5 hover:bg-gray-100 rounded transition-colors text-xs flex items-center gap-1"
					title="تولید مجدد"
				>
					<span>🔄</span>
					<span className="text-gray-600">دوباره</span>
				</button>
			)}
		</div>
	)
}

export default MessageActions
