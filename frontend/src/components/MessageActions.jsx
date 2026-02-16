import React, { useState } from "react"

/**
 * دکمه‌های عملیات پیام (با قابلیت ویرایش)
 *
 * ویژگی‌ها:
 * - کپی متن
 * - تولید مجدد (برای پیام‌های ربات)
 * - ویرایش پیام (برای پیام‌های کاربر) ✏️
 */
const MessageActions = ({
	content,
	onRegenerate,
	onEdit, // ✨ تابع جدید برای ویرایش
	isUser,
	isRegenerating = false,
}) => {
	const [copied, setCopied] = useState(false)
	const [copyError, setCopyError] = useState(false)

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(content)
			setCopied(true)
			setCopyError(false)

			// ریست بعد از 2 ثانیه
			setTimeout(() => setCopied(false), 2000)
		} catch (err) {
			console.error("Failed to copy:", err)
			setCopyError(true)
			setTimeout(() => setCopyError(false), 3000)
		}
	}

	return (
		<div className="relative flex items-center gap-2">
			{/* --- دکمه کپی --- */}
			<div className="relative flex items-center">
				{/* 1. دکمه (Peer) باید اول باشد */}
				<button
					onClick={handleCopy}
					disabled={copied}
					className="peer w-8 h-8 rounded-full flex items-center justify-center
                        bg-transparent shadow-none
                        text-gray-400 hover:text-black hover:bg-gray-200
                        transition-all duration-200
                        disabled:opacity-50 disabled:cursor-not-allowed z-10 relative"
					aria-label="کپی متن پیام"
				>
					{copied ? (
						<svg
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							strokeWidth="2.5"
							strokeLinecap="round"
							strokeLinejoin="round"
							className="text-green-600"
						>
							<polyline points="20 6 9 17 4 12"></polyline>
						</svg>
					) : (
						<svg
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							strokeWidth="2"
							strokeLinecap="round"
							strokeLinejoin="round"
						>
							<rect
								x="9"
								y="9"
								width="13"
								height="13"
								rx="2"
								ry="2"
							></rect>
							<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
						</svg>
					)}
				</button>

				{/* 2. تولتیپ (Target) باید بعد از دکمه باشد */}
				<div
					className={`
                    absolute top-full mt-2 left-1/2 -translate-x-1/2 
                    bg-black text-white text-xs px-3 py-1.5 rounded-full 
                    whitespace-nowrap transition-opacity duration-200 z-50 pointer-events-none
                    ${copied ? "opacity-100" : "opacity-0 peer-hover:opacity-100"}
                `}
				>
					{copied ? "کپی شد!" : "کپی"}
					{/* فلش رو به بالا */}
					<div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-0.5 border-4 border-transparent border-b-black"></div>
				</div>
			</div>

			{/* --- دکمه ویرایش (فقط برای پیام‌های کاربر) ✏️ --- */}
			{isUser && onEdit && (
				<div className="relative flex items-center">
					{/* 1. دکمه (Peer) */}
					<button
						onClick={onEdit}
						className="peer w-8 h-8 rounded-full flex items-center justify-center
                            bg-transparent shadow-none
                            text-gray-400 hover:text-black hover:bg-gray-200
                            transition-all duration-200 z-10 relative"
						aria-label="ویرایش پیام"
					>
						{/* ایکون مداد ساده - دقیقاً مثل ChatGPT */}
						<svg
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							strokeWidth="2"
							strokeLinecap="round"
							strokeLinejoin="round"
						>
							<path d="M12 20h9"></path>
							<path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
						</svg>
					</button>

					{/* 2. تولتیپ (Target) */}
					<div
						className="
                        absolute top-full mt-2 left-1/2 -translate-x-1/2 
                        bg-black text-white text-xs px-3 py-1.5 rounded-full 
                        whitespace-nowrap opacity-0 peer-hover:opacity-100 
                        transition-opacity duration-200 z-50 pointer-events-none
                    "
					>
						ویرایش
						{/* فلش رو به بالا */}
						<div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-0.5 border-4 border-transparent border-b-black"></div>
					</div>
				</div>
			)}

			{/* --- دکمه تولید مجدد (فقط برای پیام‌های ربات) --- */}
			{!isUser && onRegenerate && (
				<div className="relative flex items-center">
					{/* 1. دکمه (Peer) */}
					<button
						onClick={onRegenerate}
						disabled={isRegenerating}
						className="peer w-8 h-8 rounded-full flex items-center justify-center
                            bg-transparent shadow-none
                            text-gray-400 hover:text-black hover:bg-gray-200
                            transition-all duration-200
                            disabled:opacity-50 disabled:cursor-not-allowed z-10 relative"
						aria-label="تولید مجدد پاسخ"
					>
						{isRegenerating ? (
							<svg
								className="animate-spin h-4 w-4 text-gray-600"
								viewBox="0 0 24 24"
								fill="none"
							>
								<circle
									className="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									strokeWidth="4"
								/>
								<path
									className="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
						) : (
							<svg
								width="16"
								height="16"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								strokeWidth="2"
								strokeLinecap="round"
								strokeLinejoin="round"
							>
								<polyline points="23 4 23 10 17 10"></polyline>
								<polyline points="1 20 1 14 7 14"></polyline>
								<path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
							</svg>
						)}
					</button>

					{/* 2. تولتیپ (Target) */}
					<div
						className="
                        absolute top-full mt-2 left-1/2 -translate-x-1/2 
                        bg-black text-white text-xs px-3 py-1.5 rounded-full 
                        whitespace-nowrap opacity-0 peer-hover:opacity-100 
                        transition-opacity duration-200 z-50 pointer-events-none
                    "
					>
						تولید مجدد
						{/* فلش رو به بالا */}
						<div className="absolute bottom-full left-1/2 -translate-x-1/2 -mb-0.5 border-4 border-transparent border-b-black"></div>
					</div>
				</div>
			)}

			{/* Toast خطا */}
			{copyError && (
				<div
					className="absolute top-0 right-0 bg-red-50 border border-red-200 
                        text-red-600 px-2 py-1 rounded-md shadow-lg text-xs flex items-center gap-1 z-50 animate-bounce"
					role="alert"
				>
					خطا در کپی
				</div>
			)}
		</div>
	)
}

export default MessageActions
