import React, { useState, useRef, useEffect } from "react"

const InputBox = ({ onSend, isLoading }) => {
	const [message, setMessage] = useState("")
	const textareaRef = useRef(null)

	useEffect(() => {
		if (!isLoading && textareaRef.current) {
			textareaRef.current.focus()
		}
	}, [isLoading])

	useEffect(() => {
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto"
			textareaRef.current.style.height = `${Math.min(
				textareaRef.current.scrollHeight,
				200,
			)}px`
		}
	}, [message])

	const handleSubmit = (e) => {
		e.preventDefault()
		const trimmed = message.trim()
		if (!trimmed || isLoading) return

		onSend(trimmed)
		setMessage("")
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto"
		}
	}

	const handleKeyDown = (e) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault()
			handleSubmit(e)
		}
	}

	const isNearLimit = message.length > 900
	const isOverLimit = message.length > 1000

	return (
		<div className="bg-white px-4 py-4">
			<form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
				<div
					className={`
						relative flex items-end gap-2 
						bg-white rounded-2xl 
						border-2 transition-all duration-200
						${isOverLimit ? "border-t-red-400" : "border-t-gray-200"}
					`}>
					{/* دکمه ارسال */}
					<div className="pb-2 pl-2 pr-1">
						<button
							type="submit"
							disabled={
								!message.trim() || isLoading || isOverLimit
							}
							className={`
								w-10 h-10 rounded-full flex items-center justify-center shadow-md
								transition-all duration-200
								${
									message.trim() && !isOverLimit
										? "bg-[#ffc414] text-gray-900"
										: "bg-gray-100 text-gray-400 cursor-not-allowed"
								}
								${isLoading && "opacity-60"}
							`}
							aria-label="ارسال پیام">
							{isLoading ? (
								<svg
									className="animate-spin h-4 w-4"
									viewBox="0 0 24 24">
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
							) : (
								<svg
									className="w-5 h-5 text-white flex-shrink-0"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									strokeWidth="2.5"
									strokeLinecap="round"
									strokeLinejoin="round">
									<line x1="12" y1="19" x2="12" y2="5"></line>
									<polyline points="5 12 12 5 19 12"></polyline>
								</svg>
							)}
						</button>
					</div>
					{/* Textarea */}
					<textarea
						ref={textareaRef}
						value={message}
						onChange={(e) => setMessage(e.target.value)}
						onKeyDown={handleKeyDown}
						placeholder="پیام خود را بنویسید..."
						disabled={isLoading}
						rows={1}
						className="flex-1 bg-transparent border-none px-4 py-3.5 
							text-gray-800 placeholder-gray-400 resize-none focus:outline-none 
							min-h-[48px] max-h-[200px] overflow-y-auto
							disabled:opacity-50 text-[15px] leading-relaxed"
					/>
				</div>

				{/* Footer */}
				<div className="flex items-center justify-between mt-2 px-1">
					<div className="flex items-center gap-2">
						<span
							className={`text-xs font-medium ${
								isOverLimit
									? "text-red-500"
									: isNearLimit
										? "text-orange-500"
										: "text-gray-400"
							}`}>
							{message.length.toLocaleString("fa-IR")}/۱۰۰۰
						</span>
						{isOverLimit && (
							<span className="text-xs text-red-500">
								حداکثر کاراکتر
							</span>
						)}
					</div>

					<span className="text-xs text-gray-400">
						Shift + Enter برای خط جدید
					</span>
				</div>
			</form>
		</div>
	)
}

export default InputBox
