import React, { useState, useRef, useEffect, useCallback, useMemo } from "react"
import MessageActions from "./MessageActions"
import MarkdownRenderer from "./MarkdownRenderer"
import { useTypingEffect } from "../hooks/useTypingEffect"

const Message = ({
	message,
	onRegenerate,
	onEditSubmit,
	isRegenerating = false,
	enableTyping = false,
	typingEffect = "slideIn",
}) => {
	const isUser = message.role === "user"
	const [isEditing, setIsEditing] = useState(false)
	const [editedContent, setEditedContent] = useState(message.content)
	const textareaRef = useRef(null)

	const { displayedText, isTyping } = useTypingEffect(
		message.content,
		20,
		enableTyping && !isUser,
	)

	const content = useMemo(
		() => (enableTyping && !isUser ? displayedText : message.content),
		[enableTyping, isUser, displayedText, message.content],
	)

	// 🎯 Handlers
	const handleEditStart = useCallback(() => {
		setIsEditing(true)
		setEditedContent(message.content)
	}, [message.content])

	const handleEditCancel = useCallback(() => {
		setIsEditing(false)
		setEditedContent(message.content)
	}, [message.content])

	const handleEditSave = useCallback(() => {
		const trimmed = editedContent.trim()
		if (!trimmed || trimmed === message.content) {
			handleEditCancel()
			return
		}
		onEditSubmit?.(message.id, trimmed)
		setIsEditing(false)
	}, [editedContent, message, onEditSubmit, handleEditCancel])

	const handleKeyDown = useCallback(
		(e) => {
			if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
				e.preventDefault()
				handleEditSave()
			}
			if (e.key === "Escape") {
				e.preventDefault()
				handleEditCancel()
			}
		},
		[handleEditSave, handleEditCancel],
	)

	// 🎯 Effects
	useEffect(() => {
		if (isEditing && textareaRef.current) {
			textareaRef.current.focus()
			textareaRef.current.setSelectionRange(
				editedContent.length,
				editedContent.length,
			)
		}
	}, [isEditing, editedContent.length])

	useEffect(() => {
		if (isEditing && textareaRef.current) {
			textareaRef.current.style.height = "auto"
			textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
		}
	}, [isEditing, editedContent])

	// 🎯 Render content
	const renderContent = useMemo(() => {
		const markdown = (
			<MarkdownRenderer
				content={content}
				isInline={enableTyping && !isUser}
			/>
		)

		if (!enableTyping || isUser) return markdown

		return typingEffect === "slideIn" ? (
			<span className="inline-block animate-slideInRight">
				{markdown}
			</span>
		) : (
			markdown
		)
	}, [content, enableTyping, isUser, typingEffect])

	// 🎯 Edit mode
	if (isEditing) {
		return (
			<div className="w-full py-2 animate-fadeIn">
				<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
					<div className="w-full max-w-[85%]">
						<textarea
							ref={textareaRef}
							value={editedContent}
							onChange={(e) => setEditedContent(e.target.value)}
							onKeyDown={handleKeyDown}
							rows={1}
							className="w-full text-sm md:text-base leading-7 px-4 py-3 rounded-2xl resize-none text-right bg-gray-100 text-gray-900 border border-transparent focus:outline-none focus:shadow-md transition-all duration-150 min-h-[52px]"
						/>
						<div className="flex items-center gap-3 mt-3">
							<button
								onClick={handleEditSave}
								className="px-4 py-2 bg-black hover:bg-gray-800 text-white text-sm rounded-full transition-colors font-medium">
								ارسال
							</button>
							<button
								onClick={handleEditCancel}
								className="px-4 py-2 bg-white hover:bg-gray-100 text-gray-600 text-sm rounded-full border border-gray-200 transition-colors font-medium">
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
				</div>
			</div>
		)
	}

	// 🎯 Normal mode
	return (
		<div className="w-full py-2 animate-fadeIn group">
			<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
				<div
					className={`text-sm md:text-base leading-7 whitespace-pre-wrap break-words px-4 py-3 rounded-2xl w-fit max-w-[85%] ${isUser ? "bg-[#fff6d9] text-gray-900" : "text-gray-900"}`}>
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
			</div>
		</div>
	)
}

export default React.memo(Message)
