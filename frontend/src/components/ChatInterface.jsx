import React, { useState, useRef, useEffect } from "react"
import Message from "./Message"
import SkeletonMessage from "./SkeletonMessage"
import ScrollToBottom from "./ScrollToBottom"
import InputBox from "./InputBox"
import { sendMessage } from "../services/api"

/**
 * کامپوننت اصلی چت (نسخه نهایی با تمام قابلیت‌ها)
 */
const ChatInterface = () => {
	const [messages, setMessages] = useState([])
	const [isLoading, setIsLoading] = useState(false)
	const [error, setError] = useState(null)
	const [showScrollButton, setShowScrollButton] = useState(false)
	const messagesEndRef = useRef(null)
	const messagesContainerRef = useRef(null)

	// Auto-scroll به آخرین پیام
	const scrollToBottom = (behavior = "smooth") => {
		messagesEndRef.current?.scrollIntoView({ behavior })
	}

	// Scroll event برای نمایش دکمه scroll to bottom
	useEffect(() => {
		const container = messagesContainerRef.current
		if (!container) return

		const handleScroll = () => {
			const { scrollTop, scrollHeight, clientHeight } = container
			const isNearBottom = scrollHeight - scrollTop - clientHeight < 100
			setShowScrollButton(!isNearBottom && messages.length > 0)
		}

		container.addEventListener("scroll", handleScroll)
		return () => container.removeEventListener("scroll", handleScroll)
	}, [messages.length])

	// Auto-scroll وقتی پیام جدید میاد
	useEffect(() => {
		if (messages.length > 0) {
			scrollToBottom()
		}
	}, [messages])

	// ارسال پیام
	const handleSend = async (content) => {
		const userMessage = {
			role: "user",
			content,
			timestamp: new Date(),
		}

		setMessages((prev) => [...prev, userMessage])
		setIsLoading(true)
		setError(null)

		try {
			const response = await sendMessage(content)

			if (response.success) {
				const botMessage = {
					role: "assistant",
					content: response.answer,
					timestamp: new Date(response.timestamp),
					sources: response.sources,
					metadata: response.metadata,
				}

				setMessages((prev) => [...prev, botMessage])
			} else {
				throw new Error(response.error || "خطای نامشخص")
			}
		} catch (err) {
			console.error("Error sending message:", err)
			setError(err.message || "خطا در ارسال پیام")

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

	// Regenerate پاسخ (edit همون پیام)
	const handleRegenerate = async (messageIndex) => {
		if (messageIndex < 1) return

		// پیدا کردن سوال مربوط
		let userMessageIndex = -1
		for (let i = messageIndex - 1; i >= 0; i--) {
			if (messages[i].role === "user") {
				userMessageIndex = i
				break
			}
		}

		if (userMessageIndex === -1) return

		const userMessage = messages[userMessageIndex]
		setIsLoading(true)

		try {
			const response = await sendMessage(userMessage.content)

			if (response.success) {
				// ✅ آپدیت همون پیام
				setMessages((prev) => {
					const newMessages = [...prev]
					newMessages[messageIndex] = {
						...newMessages[messageIndex],
						content: response.answer,
						timestamp: new Date(response.timestamp),
						sources: response.sources,
						metadata: response.metadata,
					}
					return newMessages
				})
			} else {
				throw new Error(response.error || "خطای نامشخص")
			}
		} catch (err) {
			console.error("Error regenerating:", err)

			setMessages((prev) => {
				const newMessages = [...prev]
				newMessages[messageIndex] = {
					...newMessages[messageIndex],
					content: `❌ ${err.message || "خطا در تولید مجدد"}`,
				}
				return newMessages
			})
		} finally {
			setIsLoading(false)
		}
	}

	return (
		<div className="flex flex-col h-screen bg-white">
			{/* Header */}
			<header className="bg-gradient-to-l from-white to-gray-50 border-b border-gray-200 px-4 py-4 shadow-sm">
				<div className="max-w-4xl mx-auto flex items-center justify-between">
					<div className="flex items-center gap-3">
						<div
							className="w-10 h-10 bg-gradient-to-br from-green-400 to-green-600 rounded-xl 
							flex items-center justify-center shadow-md transform hover:scale-110 
							transition-transform duration-300"
						>
							<span className="text-white text-xl font-bold">
								م
							</span>
						</div>
						<div>
							<h1 className="text-xl font-bold text-gray-800">
								متا
							</h1>
							<p className="text-xs text-gray-500">
								دستیار هوشمند شهرسازی
							</p>
						</div>
					</div>

					<div className="flex items-center gap-2 bg-green-50 px-3 py-1.5 rounded-full">
						<div className="relative flex items-center justify-center">
							<div className="w-2 h-2 bg-green-500 rounded-full"></div>
							<div className="absolute inset-0 w-2 h-2 bg-green-500 rounded-full animate-pulse-ring"></div>
						</div>
						<span className="text-xs text-green-700 font-medium">
							آنلاین
						</span>
					</div>
				</div>
			</header>

			{/* Messages Area - با custom-scrollbar */}
			<div
				ref={messagesContainerRef}
				className="flex-1 overflow-y-auto px-4 py-6 custom-scrollbar bg-white"
			>
				<div className="max-w-4xl mx-auto">
					{messages.length === 0 ? (
						// Empty State
						<div className="text-center mt-20 animate-fadeIn">
							<div className="relative inline-block mb-6">
								<div className="absolute inset-0 bg-green-400 rounded-full blur-2xl opacity-20 animate-pulse"></div>
								<div
									className="relative w-24 h-24 bg-gradient-to-br from-green-400 to-green-600 
									rounded-full flex items-center justify-center shadow-xl 
									transform hover:scale-110 transition-transform duration-300"
								>
									<span className="text-4xl">🤖</span>
								</div>
							</div>

							<h2 className="text-3xl font-bold mb-3">
								<span
									className="bg-gradient-to-l from-gray-800 via-gray-700 to-gray-800 
									bg-clip-text text-transparent"
								>
									سلام! من متا هستم
								</span>
							</h2>

							<p className="text-gray-600 mb-8 text-lg">
								از من درباره انقلاب اسلامی و شهرسازی بپرسید
							</p>

							<div className="mt-8 flex flex-col gap-2 items-center">
								<p className="text-xs text-gray-400 mb-2">
									مثال‌های سوال:
								</p>
								<div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-4xl mx-auto px-4">
									{[
										{
											emoji: "💡",
											text: "انقلاب اسلامی چه تأثیری داشت؟",
										},
										{
											emoji: "📚",
											text: "ویژگی‌های انقلاب اسلامی چیست؟",
										},
										{
											emoji: "🏛️",
											text: "نقش امام خمینی در انقلاب",
										},
									].map((example, idx) => (
										<button
											key={idx}
											onClick={() =>
												handleSend(example.text)
											}
											className="group relative overflow-hidden bg-white border-2 border-gray-200 
												hover:border-green-400 hover:bg-green-50 p-4 rounded-2xl 
												transition-all duration-300 shadow-sm hover:shadow-xl
												transform hover:-translate-y-1 active:scale-95"
										>
											<span
												className="absolute inset-0 bg-gradient-to-r from-transparent via-white 
												to-transparent opacity-0 group-hover:opacity-20 transform translate-x-[-100%] 
												group-hover:translate-x-[100%] transition-transform duration-700"
											></span>

											<div className="relative">
												<div className="text-2xl mb-2 group-hover:scale-110 transition-transform duration-300">
													{example.emoji}
												</div>
												<p className="text-sm text-gray-700 group-hover:text-green-700 transition-colors">
													{example.text}
												</p>
											</div>
										</button>
									))}
								</div>
							</div>
						</div>
					) : (
						<>
							{messages.map((msg, idx) => (
								<Message
									key={idx}
									message={msg}
									onRegenerate={
										msg.role === "assistant"
											? () => handleRegenerate(idx)
											: null
									}
									// ✅ فقط برای آخرین پیام ربات typing effect فعاله
									enableTyping={
										msg.role === "assistant" &&
										idx === messages.length - 1 &&
										!isLoading
									}
								/>
							))}

							{/* Skeleton Loading */}
							{isLoading && <SkeletonMessage />}
						</>
					)}

					<div ref={messagesEndRef} />
				</div>
			</div>

			{/* Scroll to Bottom Button */}
			<ScrollToBottom
				show={showScrollButton}
				onClick={() => scrollToBottom()}
			/>

			{/* Input Box */}
			<InputBox onSend={handleSend} isLoading={isLoading} />
		</div>
	)
}

export default ChatInterface
