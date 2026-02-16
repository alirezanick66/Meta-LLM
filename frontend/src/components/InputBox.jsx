import React, { useState, useRef, useEffect } from "react"

/**
 * کامپوننت ورودی پیام (نسخه بهبود یافته)
 *
 * بهبودها:
 * - focus بعد از ارسال
 * - progress cap به 100%
 * - max-height برای textarea
 * - جلوگیری از infinite loop در auto-resize
 *
 * @param {Function} onSend - تابعی که با فشردن ارسال صدا زده می‌شود
 * @param {boolean} isLoading - آیا در حال ارسال است؟
 */
const InputBox = ({ onSend, isLoading }) => {
	const [message, setMessage] = useState("")
	const textareaRef = useRef(null)

	// ✅ Auto-focus on mount (یکبار وقتی component mount میشه)
	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.focus()
		}
	}, [])

	// ✅ Re-focus وقتی isLoading تغییر می‌کنه (بعد از ارسال پیام)
	useEffect(() => {
		if (!isLoading && textareaRef.current) {
			textareaRef.current.focus()
		}
	}, [isLoading])

	// Auto-resize textarea (با max-height محدود)
	useEffect(() => {
		if (textareaRef.current) {
			// Reset height to auto to get correct scrollHeight
			textareaRef.current.style.height = "auto"

			// محاسبه height جدید
			const newHeight = textareaRef.current.scrollHeight

			// تنظیم height با max-height محدود (200px)
			textareaRef.current.style.height = `${Math.min(newHeight, 200)}px`
		}
	}, [message])

	const handleSubmit = (e) => {
		e.preventDefault()

		const trimmed = message.trim()
		if (!trimmed || isLoading) return

		onSend(trimmed)
		setMessage("")

		// Reset height
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto"
			// ✅ بازگشت focus به textarea بعد از ارسال
			textareaRef.current.focus()
		}
	}

	const handleKeyDown = (e) => {
		// Enter برای ارسال، Shift+Enter برای خط جدید
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault()
			handleSubmit(e)
		}
	}

	// ✅ محاسبه درصد progress با cap به 100%
	const progressPercentage = Math.min((message.length / 1000) * 100, 100)
	const isNearLimit = message.length > 900
	const isOverLimit = message.length > 1000

	return (
		<div className="bg-white p-4">
			<form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
				{/* Container با border focus effect */}
				<div
					className={`relative bg-gray-10 rounded-2xl border-2 transition-all duration-300
					${
						isOverLimit
							? "border-red-400 bg-red-50"
							: message.length > 0
								? "border-green-400 bg-white shadow-md"
								: "border-gray-200 hover:border-gray-300"
					}`}
				>
					<div className="flex items-end gap-2 p-2">
						{/* دکمه ارسال با gradient */}
						<button
							type="submit"
							disabled={
								!message.trim() || isLoading || isOverLimit
							}
							className="bg-gradient-to-br from-green-400 to-green-600 
								hover:from-green-500 hover:to-green-700 
								disabled:from-gray-300 disabled:to-gray-400 
								text-white rounded-xl px-5 py-3 
								transition-all duration-300 shadow-md hover:shadow-lg 
								disabled:shadow-none transform hover:scale-105 active:scale-95
								flex-shrink-0 h-[46px]"
							aria-label="ارسال پیام"
						>
							{isLoading ? (
								<span className="flex items-center gap-2">
									<svg
										className="animate-spin h-5 w-5"
										viewBox="0 0 24 24"
										aria-hidden="true"
									>
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
								"➤"
							)}
						</button>

						{/* Textarea با max-height محدود */}
						<textarea
							ref={textareaRef}
							value={message}
							onChange={(e) => setMessage(e.target.value)}
							onKeyDown={handleKeyDown}
							placeholder="پیام خود را بنویسید..."
							disabled={isLoading}
							rows={1}
							className="flex-1 bg-transparent border-none px-4 py-3 
								text-gray-900 placeholder-gray-400 resize-none focus:outline-none 
								max-h-[200px] overflow-y-auto scrollbar-thin 
								disabled:opacity-50 disabled:cursor-not-allowed"
							aria-label="فیلد ورودی پیام"
						/>
					</div>

					{/* Progress bar */}
					<div className="h-1 bg-gray-200 rounded-b-2xl overflow-hidden">
						<div
							className={`h-full transition-all duration-300 ${
								isOverLimit
									? "bg-gradient-to-r from-red-500 to-red-700"
									: isNearLimit
										? "bg-gradient-to-r from-orange-400 to-orange-600"
										: "bg-gradient-to-r from-green-400 to-green-600"
							}`}
							style={{ width: `${progressPercentage}%` }}
							role="progressbar"
							aria-valuenow={message.length}
							aria-valuemin="0"
							aria-valuemax="1000"
						/>
					</div>
				</div>

				{/* Character counter با رنگ پویا */}
				<div className="flex items-center justify-between mt-2 px-1">
					<div
						className={`text-xs transition-colors ${
							isOverLimit
								? "text-red-600 font-bold"
								: isNearLimit
									? "text-orange-500 font-semibold"
									: "text-gray-400"
						}`}
					>
						{message.length}/1000
						{isOverLimit && (
							<span className="mr-2 text-red-600">
								⚠️ حداکثر تعداد کاراکتر
							</span>
						)}
					</div>

					{/* راهنما */}
					<div className="text-xs text-gray-400">
						Enter برای ارسال • Shift+Enter برای خط جدید
					</div>
				</div>
			</form>
		</div>
	)
}

export default InputBox
