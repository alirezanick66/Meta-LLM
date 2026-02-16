import React, { useMemo, useState, useRef, useEffect } from "react"
import MessageActions from "./MessageActions"
import { useTypingEffect } from "../hooks/useTypingEffect"

/**
 * کامپوننت نمایش پیام (با ویرایش inline شبیه ChatGPT - اصلاح شده)
 *
 * اصلاحات:
 * - اسکرول بار سمت راست (با استفاده از dir="ltr" در textarea)
 * - رنگ‌بندی دقیق دکمه‌ها و باکس متن طبق استایل ChatGPT
 */
const Message = ({
	message,
	onRegenerate,
	onEditSubmit,
	isRegenerating = false,
	enableTyping = false,
	typingEffect = "slideIn",
}) => {
	const isUser = message.role === "user"

	// Edit mode
	const [isEditing, setIsEditing] = useState(false)
	const [editedContent, setEditedContent] = useState(message.content)
	const textareaRef = useRef(null)

	// Typing effect
	const { displayedText, isTyping } = useTypingEffect(
		message.content,
		20,
		enableTyping && !isUser,
	)

	const content = useMemo(() => {
		return enableTyping && !isUser ? displayedText : message.content
	}, [enableTyping, isUser, displayedText, message.content])

	// فوکوس روی textarea هنگام ویرایش
	useEffect(() => {
		if (isEditing && textareaRef.current) {
			textareaRef.current.focus()
			textareaRef.current.setSelectionRange(
				editedContent.length,
				editedContent.length,
			)
		}
	}, [isEditing, editedContent.length])

	// Auto resize
	useEffect(() => {
		if (isEditing && textareaRef.current) {
			textareaRef.current.style.height = "auto"
			textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
		}
	}, [isEditing, editedContent])

	const handleEditStart = () => {
		setIsEditing(true)
		setEditedContent(message.content)
	}

	const handleEditCancel = () => {
		setIsEditing(false)
		setEditedContent(message.content)
	}

	const handleEditSave = () => {
		const trimmed = editedContent.trim()
		if (!trimmed || trimmed === message.content) {
			handleEditCancel()
			return
		}

		onEditSubmit?.(message.id, trimmed)
		setIsEditing(false)
	}

	const handleKeyDown = (e) => {
		if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
			e.preventDefault()
			handleEditSave()
		}

		if (e.key === "Escape") {
			e.preventDefault()
			handleEditCancel()
		}
	}

	const renderContent = useMemo(() => {
		if (!enableTyping || isUser) return content

		switch (typingEffect) {
			case "slideIn":
				return (
					<span className="inline-block animate-slideInRight">
						{content}
					</span>
				)
			default:
				return content
		}
	}, [enableTyping, isUser, content, typingEffect])

	return (
		<div className="w-full py-2 animate-fadeIn group">
			<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
				{isEditing ? (
					<div className="w-full max-w-[85%]">
						<textarea
							ref={textareaRef}
							value={editedContent}
							onChange={(e) => setEditedContent(e.target.value)}
							onKeyDown={handleKeyDown}
							rows={1}
							style={{ minHeight: "52px" }}
							className="w-full text-sm md:text-base leading-7 px-4 py-3 rounded-2xl resize-none text-right
                            bg-gray-100 text-gray-900 border border-transparent
                            focus:outline-none focus:shadow-md focus:ring-0
                            transition-all duration-150"
						/>

						<div className="flex items-center gap-3 mt-3">
							{/* دکمه ذخیره - مشکی */}
							<button
								onClick={handleEditSave}
								className="px-4 py-2 bg-black hover:bg-gray-800 text-white text-sm rounded-full transition-colors duration-150 font-medium"
							>
								ارسال
							</button>

							{/* دکمه لغو - سفید */}
							<button
								onClick={handleEditCancel}
								className="px-4 py-2 bg-white hover:bg-gray-100 text-gray-600 text-sm rounded-full border border-gray-200 transition-colors duration-150 font-medium"
							>
								لغو
							</button>
						</div>

						<p className="text-[11px] text-gray-400 mt-2">
							<kbd className="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200">
								shift + Enter
							</kbd>
							{" برای خط جدید • "}
							<kbd className="px-1.5 py-0.5 bg-gray-100 rounded border border-gray-200">
								ESC
							</kbd>
							{" برای بستن"}
						</p>
					</div>
				) : (
					<>
						<div
							className={`text-sm md:text-base leading-7 whitespace-pre-wrap break-words px-4 py-3 rounded-2xl w-fit max-w-[85%]
                            ${isUser ? "bg-[#fff6d9] text-gray-900" : "text-gray-900"}`}
						>
							{renderContent}

							{isTyping && typingEffect === "default" && (
								<span className="inline-block w-0.5 h-4 bg-gray-900 ml-1 animate-pulse">
									▌
								</span>
							)}
						</div>

						{!isTyping && (
							<div className="opacity-0 group-hover:opacity-100 transition-opacity duration-200">
								<MessageActions
									content={message.content}
									onRegenerate={!isUser ? onRegenerate : null}
									onEdit={isUser ? handleEditStart : null}
									isUser={isUser}
									isRegenerating={isRegenerating}
								/>
							</div>
						)}
					</>
				)}
			</div>
		</div>
	)
}

export default React.memo(Message)
