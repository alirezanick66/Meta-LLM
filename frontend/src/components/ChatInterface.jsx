import React, { useState, useRef, useEffect } from "react"
import Message from "./Message"
import InputBox from "./InputBox"
import { sendMessage } from "../services/api"

/**
 * کامپوننت اصلی چت
 */
const ChatInterface = () => {
	const [messages, setMessages] = useState([])
	const [isLoading, setIsLoading] = useState(false)
	const [error, setError] = useState(null)
	const messagesEndRef = useRef(null)

	// Auto-scroll به آخرین پیام
	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
	}

	useEffect(() => {
		scrollToBottom()
	}, [messages])

	// ارسال پیام
	const handleSend = async (content) => {
		// پیام کاربر رو اضافه کن
		const userMessage = {
			role: "user",
			content,
			timestamp: new Date(),
		}

		setMessages((prev) => [...prev, userMessage])
		setIsLoading(true)
		setError(null)

		try {
			// ارسال به API
			const response = await sendMessage(content)

			if (response.success) {
				// پیام ربات رو اضافه کن
				const botMessage = {
					role: "assistant",
					content: response.answer,
					timestamp: new Date(response.timestamp),
					sources: response.sources,
					metadata: response.metadata,
				}

				setMessages((prev) => [...prev, botMessage])
			} else {
				// خطا از API
				throw new Error(response.error || "خطای نامشخص")
			}
		} catch (err) {
			console.error("Error sending message:", err)
			setError(err.message || "خطا در ارسال پیام")

			// پیام خطا رو به عنوان پیام ربات نشون بده
			const errorMessage = {
				role: "assistant",
				content: `❌ ${err.message || "متأسفانه مشکلی پیش آمده. لطفاً دوباره تلاش کنید."}`,
				timestamp: new Date(),
			}

			setMessages((prev) => [...prev, errorMessage])
		} finally {
			setIsLoading(false)
		}
	}

	return (
		<div className="flex flex-col h-screen bg-primary-bg">
			{/* Messages Area */}
			<div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin">
				<div className="max-w-4xl mx-auto">
					{messages.length === 0 ? (
						// پیام خوش‌آمدگویی
						<div className="text-center text-gray-600 mt-20">
							<div className="text-6xl mb-4">👋</div>
							<h2 className="text-2xl font-bold mb-2 text-gray-800">
								سلام! من متا هستم
							</h2>
							<p className="text-sm">
								از من در مورد انقلاب اسلامی بپرسید
							</p>
							<div className="mt-8 flex flex-col gap-2 items-center">
								<p className="text-xs text-gray-400">
									مثال‌های سوال:
								</p>
								<div className="flex flex-wrap gap-2 justify-center max-w-2xl">
									{[
										"انقلاب اسلامی چه تأثیری داشت؟",
										"ویژگی‌های انقلاب اسلامی چیست؟",
										"نقش امام خمینی در انقلاب",
									].map((example, idx) => (
										<button
											key={idx}
											onClick={() => handleSend(example)}
											className="text-xs bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 
                               px-3 py-2 rounded-lg transition-all text-gray-700 shadow-sm"
										>
											{example}
										</button>
									))}
								</div>
							</div>
						</div>
					) : (
						// لیست پیام‌ها
						<>
							{messages.map((msg, idx) => (
								<Message key={idx} message={msg} />
							))}

							{/* Loading indicator - استایل مناسب تم روشن */}
							{isLoading && (
								<div className="flex justify-start mb-4">
									<div className="bg-bot-bg border border-gray-200 shadow-sm rounded-2xl px-4 py-3">
										<div className="flex gap-1 mt-2">
											<div className="w-2 h-2 bg-gray-400 rounded-full animate-typing"></div>
											<div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-delay-1"></div>
											<div className="w-2 h-2 bg-gray-400 rounded-full animate-typing-delay-2"></div>
										</div>
									</div>
								</div>
							)}
						</>
					)}

					{/* Scroll target */}
					<div ref={messagesEndRef} />
				</div>
			</div>

			{/* Input Box */}
			<InputBox onSend={handleSend} isLoading={isLoading} />
		</div>
	)
}

export default ChatInterface
