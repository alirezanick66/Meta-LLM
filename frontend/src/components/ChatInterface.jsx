import React, { useState, useRef, useEffect, useCallback } from "react"
import Message from "./Message"
import SkeletonMessage from "./SkeletonMessage"
import ScrollToBottom from "./ScrollToBottom"
import InputBox from "./InputBox"
import { sendMessage } from "../services/api"

/**
 * کامپوننت اصلی چت (نسخه اصلاح شده)
 *
 * اصلاحیه: جابجایی handleSend و handleEditSubmit برای رفع خطای ReferenceError
 */
const ChatInterface = () => {
	const [messages, setMessages] = useState([])
	const [isLoading, setIsLoading] = useState(false)
	const [error, setError] = useState(null)
	const [showScrollButton, setShowScrollButton] = useState(false)

	const messagesEndRef = useRef(null)
	const messagesContainerRef = useRef(null)
	const isMountedRef = useRef(true)
	const abortControllerRef = useRef(null)

	// Cleanup on unmount
	useEffect(() => {
		isMountedRef.current = true
		return () => {
			isMountedRef.current = false
			if (abortControllerRef.current) {
				abortControllerRef.current.abort()
			}
		}
	}, [])

	// Auto-scroll به آخرین پیام
	const scrollToBottom = useCallback((behavior = "smooth") => {
		messagesEndRef.current?.scrollIntoView({ behavior })
	}, [])

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
	}, [messages.length, scrollToBottom])

	// تولید unique ID برای messages
	const generateMessageId = useCallback(() => {
		return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
	}, [])

	// ⚠️ مهم: این تابع باید قبل از handleEditSubmit تعریف شود
	// ارسال پیام (با useCallback)
	const handleSend = useCallback(
		async (content) => {
			console.log("🚀 handleSend called with:", content)

			const userMessage = {
				id: generateMessageId(),
				role: "user",
				content,
				timestamp: new Date(),
			}

			console.log("📝 Setting user message:", userMessage)
			setMessages((prev) => [...prev, userMessage])
			setIsLoading(true)
			setError(null)

			abortControllerRef.current = new AbortController()

			try {
				console.log("📡 Calling sendMessage API...")
				const response = await sendMessage(
					content,
					0.3,
					abortControllerRef.current.signal,
				)

				console.log("✅ API Response received:", response)

				if (!isMountedRef.current) {
					console.warn(
						"⚠️ Component unmounted, skipping state update",
					)
					return
				}

				if (response.success) {
					const botMessage = {
						id: generateMessageId(),
						role: "assistant",
						content: response.answer,
						timestamp: new Date(response.timestamp),
						sources: response.sources,
						metadata: response.metadata,
					}

					console.log("🤖 Setting bot message:", botMessage)
					setMessages((prev) => [...prev, botMessage])
				} else {
					throw new Error(response.error || "خطای نامشخص")
				}
			} catch (err) {
				console.error("❌ Error in handleSend:", err)

				if (err.name === "AbortError" || err.name === "CanceledError") {
					console.log("🚫 Request was canceled")
					return
				}

				if (!isMountedRef.current) return

				setError(err.message || "خطا در ارسال پیام")

				const errorMessage = {
					id: generateMessageId(),
					role: "assistant",
					content: `❌ ${err.message || "متأسفانه مشکلی پیش آمده. لطفاً دوباره تلاش کنید."}`,
					timestamp: new Date(),
				}

				setMessages((prev) => [...prev, errorMessage])
			} finally {
				if (isMountedRef.current) {
					setIsLoading(false)
				}
			}
		},
		[generateMessageId],
	)

	// ✨ Submit کردن پیام ویرایش شده (حالا می‌تواند handleSend را ببیند چون بالا تعریف شده)
	const handleEditSubmit = useCallback(
		(messageId, newContent) => {
			console.log("✏️ handleEditSubmit called:", messageId, newContent)

			const messageIndex = messages.findIndex(
				(msg) => msg.id === messageId,
			)
			if (messageIndex === -1) return

			// حذف پیام کاربر و تمام پیام‌های بعدش
			setMessages((prev) => prev.slice(0, messageIndex))

			// ارسال پیام جدید
			handleSend(newContent)

			console.log("📝 Edited message sent:", newContent)
		},
		[messages, handleSend],
	)

	// Regenerate پاسخ (با useCallback)
	const handleRegenerate = useCallback(
		async (messageId) => {
			const messageIndex = messages.findIndex(
				(msg) => msg.id === messageId,
			)
			if (messageIndex < 1) return

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

			abortControllerRef.current = new AbortController()

			try {
				const response = await sendMessage(
					userMessage.content,
					0.3,
					abortControllerRef.current.signal,
				)

				if (!isMountedRef.current) return

				if (response.success) {
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
				if (err.name === "AbortError" || err.name === "CanceledError") {
					console.log("Request was canceled")
					return
				}

				console.error("Error regenerating:", err)

				if (!isMountedRef.current) return

				setMessages((prev) => {
					const newMessages = [...prev]
					newMessages[messageIndex] = {
						...newMessages[messageIndex],
						content: `❌ ${err.message || "خطا در تولید مجدد"}`,
					}
					return newMessages
				})
			} finally {
				if (isMountedRef.current) {
					setIsLoading(false)
				}
			}
		},
		[messages],
	)

	return (
		<div className="flex flex-col h-screen bg-white">
			{/* Messages Area */}
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
									<span className="text-white text-5xl font-bold">
										م
									</span>
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
							{messages.map((msg) => (
								<Message
									key={msg.id}
									message={msg}
									onRegenerate={
										msg.role === "assistant"
											? () => handleRegenerate(msg.id)
											: null
									}
									onEditSubmit={
										msg.role === "user"
											? handleEditSubmit
											: null
									}
									isRegenerating={
										isLoading &&
										msg.id ===
											messages[messages.length - 1]?.id
									}
									enableTyping={
										msg.role === "assistant" &&
										msg.id ===
											messages[messages.length - 1]?.id &&
										!isLoading
									}
								/>
							))}

							{isLoading && <SkeletonMessage />}
						</>
					)}

					<div ref={messagesEndRef} />
				</div>
			</div>

			<ScrollToBottom
				show={showScrollButton}
				onClick={() => scrollToBottom()}
			/>

			<InputBox onSend={handleSend} isLoading={isLoading} />
		</div>
	)
}

export default ChatInterface
