import React, { useMemo, useState, useRef, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import MessageActions from "./MessageActions"
import { useTypingEffect } from "../hooks/useTypingEffect"

/**
 * کامپوننت نمایش پیام (با Markdown Support)
 *
 * ویژگی‌های جدید:
 * - پشتیبانی کامل از Markdown (bold, italic, lists, code, links, ...)
 * - Code blocks با syntax highlighting
 * - Copy button برای code blocks
 * - استایل‌های سفارشی برای هر element
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

	// کامپوننت سفارشی برای code blocks با copy button
	const CodeBlock = ({ inline, className, children, ...props }) => {
		const [copied, setCopied] = useState(false)
		const match = /language-(\w+)/.exec(className || "")
		const language = match ? match[1] : ""

		const handleCopyCode = async () => {
			try {
				await navigator.clipboard.writeText(String(children))
				setCopied(true)
				setTimeout(() => setCopied(false), 2000)
			} catch (err) {
				console.error("Failed to copy code:", err)
			}
		}

		if (!inline) {
			return (
				<div className="relative group my-3">
					{/* Language badge */}
					{language && (
						<div className="absolute top-2 right-2 bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">
							{language}
						</div>
					)}

					{/* Copy button */}
					<button
						onClick={handleCopyCode}
						className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 
							bg-gray-700 hover:bg-gray-600 text-white text-xs px-2 py-1 rounded 
							transition-opacity duration-200 flex items-center gap-1"
						aria-label="کپی کد">
						{copied ? (
							<>
								<svg
									width="12"
									height="12"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									strokeWidth="2.5">
									<polyline points="20 6 9 17 4 12"></polyline>
								</svg>
								کپی شد
							</>
						) : (
							<>
								<svg
									width="12"
									height="12"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									strokeWidth="2">
									<rect
										x="9"
										y="9"
										width="13"
										height="13"
										rx="2"
										ry="2"></rect>
									<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
								</svg>
								کپی
							</>
						)}
					</button>

					<pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
						<code
							className="font-mono text-sm leading-relaxed"
							{...props}>
							{children}
						</code>
					</pre>
				</div>
			)
		}

		// Inline code
		return (
			<code
				className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono"
				{...props}>
				{children}
			</code>
		)
	}

	const renderContent = useMemo(() => {
		if (!enableTyping || isUser) {
			return (
				<ReactMarkdown
					remarkPlugins={[remarkGfm]}
					components={{
						// Typography
						strong: ({ node, ...props }) => (
							<strong
								className="font-bold text-gray-900"
								{...props}
							/>
						),
						em: ({ node, ...props }) => (
							<em className="italic text-gray-700" {...props} />
						),
						del: ({ node, ...props }) => (
							<del
								className="line-through text-gray-500"
								{...props}
							/>
						),

						// Code
						code: CodeBlock,

						// Lists
						ul: ({ node, ...props }) => (
							<ul
								className="list-disc list-inside my-2 space-y-1 mr-4"
								{...props}
							/>
						),
						ol: ({ node, ...props }) => (
							<ol
								className="list-decimal list-inside my-2 space-y-1 mr-4"
								{...props}
							/>
						),
						li: ({ node, ...props }) => (
							<li
								className="text-gray-800 leading-relaxed"
								{...props}
							/>
						),

						// Headings
						h1: ({ node, ...props }) => (
							<h1
								className="text-2xl font-bold mt-4 mb-2 text-gray-900"
								{...props}
							/>
						),
						h2: ({ node, ...props }) => (
							<h2
								className="text-xl font-bold mt-3 mb-2 text-gray-900"
								{...props}
							/>
						),
						h3: ({ node, ...props }) => (
							<h3
								className="text-lg font-bold mt-2 mb-1 text-gray-900"
								{...props}
							/>
						),

						// Paragraphs
						p: ({ node, ...props }) => (
							<p className="my-1.5 leading-7" {...props} />
						),

						// Links
						a: ({ node, ...props }) => (
							<a
								className="text-blue-600 hover:text-blue-800 hover:underline"
								target="_blank"
								rel="noopener noreferrer"
								{...props}
							/>
						),

						// Blockquote
						blockquote: ({ node, ...props }) => (
							<blockquote
								className="border-r-4 border-gray-300 pr-4 my-2 text-gray-700 italic"
								{...props}
							/>
						),

						// Table
						table: ({ node, ...props }) => (
							<div className="overflow-x-auto my-4">
								<table
									className="min-w-full border-collapse border-2 border-gray-400"
									{...props}
								/>
							</div>
						),
						thead: ({ node, ...props }) => (
							<thead className="bg-gray-200" {...props} />
						),
						tbody: ({ node, ...props }) => (
							<tbody className="bg-white" {...props} />
						),
						tr: ({ node, ...props }) => (
							<tr
								className="hover:bg-gray-50 transition-colors"
								{...props}
							/>
						),
						th: ({ node, ...props }) => (
							<th
								className="border-2 border-gray-500 px-4 py-3 text-right font-bold text-gray-900 bg-gray-100"
								{...props}
							/>
						),
						td: ({ node, ...props }) => (
							<td
								className="border border-gray-400 px-4 py-3 text-right text-gray-800"
								{...props}
							/>
						),

						// Horizontal Rule
						hr: ({ node, ...props }) => (
							<hr className="my-4 border-gray-300" {...props} />
						),
					}}>
					{content}
				</ReactMarkdown>
			)
		}

		// با typing effect
		switch (typingEffect) {
			case "slideIn":
				return (
					<span className="inline-block animate-slideInRight">
						<ReactMarkdown
							remarkPlugins={[remarkGfm]}
							components={{
								strong: ({ node, ...props }) => (
									<strong
										className="font-bold text-gray-900"
										{...props}
									/>
								),
								em: ({ node, ...props }) => (
									<em
										className="italic text-gray-700"
										{...props}
									/>
								),
								code: CodeBlock,
								p: ({ node, ...props }) => (
									<p className="inline" {...props} />
								),
								// Table components
								table: ({ node, ...props }) => (
									<div className="overflow-x-auto my-4">
										<table
											className="min-w-full border-collapse border-2 border-gray-400"
											{...props}
										/>
									</div>
								),
								thead: ({ node, ...props }) => (
									<thead className="bg-gray-200" {...props} />
								),
								tbody: ({ node, ...props }) => (
									<tbody className="bg-white" {...props} />
								),
								tr: ({ node, ...props }) => (
									<tr
										className="hover:bg-gray-50 transition-colors"
										{...props}
									/>
								),
								th: ({ node, ...props }) => (
									<th
										className="border-2 border-gray-500 px-4 py-3 text-right font-bold text-gray-900 bg-gray-100"
										{...props}
									/>
								),
								td: ({ node, ...props }) => (
									<td
										className="border border-gray-400 px-4 py-3 text-right text-gray-800"
										{...props}
									/>
								),
								ul: ({ node, ...props }) => (
									<ul
										className="list-disc list-inside my-2 space-y-1 mr-4"
										{...props}
									/>
								),
								ol: ({ node, ...props }) => (
									<ol
										className="list-decimal list-inside my-2 space-y-1 mr-4"
										{...props}
									/>
								),
								li: ({ node, ...props }) => (
									<li
										className="text-gray-800 leading-relaxed"
										{...props}
									/>
								),
							}}>
							{content}
						</ReactMarkdown>
					</span>
				)
			default:
				return (
					<ReactMarkdown
						remarkPlugins={[remarkGfm]}
						components={{
							strong: ({ node, ...props }) => (
								<strong
									className="font-bold text-gray-900"
									{...props}
								/>
							),
							em: ({ node, ...props }) => (
								<em
									className="italic text-gray-700"
									{...props}
								/>
							),
							code: CodeBlock,
							p: ({ node, ...props }) => (
								<p className="inline" {...props} />
							),
							// Table components
							table: ({ node, ...props }) => (
								<div className="overflow-x-auto my-4">
									<table
										className="min-w-full border-collapse border-2 border-gray-400"
										{...props}
									/>
								</div>
							),
							thead: ({ node, ...props }) => (
								<thead className="bg-gray-200" {...props} />
							),
							tbody: ({ node, ...props }) => (
								<tbody className="bg-white" {...props} />
							),
							tr: ({ node, ...props }) => (
								<tr
									className="hover:bg-gray-50 transition-colors"
									{...props}
								/>
							),
							th: ({ node, ...props }) => (
								<th
									className="border-2 border-gray-500 px-4 py-3 text-right font-bold text-gray-900 bg-gray-100"
									{...props}
								/>
							),
							td: ({ node, ...props }) => (
								<td
									className="border border-gray-400 px-4 py-3 text-right text-gray-800"
									{...props}
								/>
							),
							ul: ({ node, ...props }) => (
								<ul
									className="list-disc list-inside my-2 space-y-1 mr-4"
									{...props}
								/>
							),
							ol: ({ node, ...props }) => (
								<ol
									className="list-decimal list-inside my-2 space-y-1 mr-4"
									{...props}
								/>
							),
							li: ({ node, ...props }) => (
								<li
									className="text-gray-800 leading-relaxed"
									{...props}
								/>
							),
						}}>
						{content}
					</ReactMarkdown>
				)
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
							<button
								onClick={handleEditSave}
								className="px-4 py-2 bg-black hover:bg-gray-800 text-white text-sm rounded-full transition-colors duration-150 font-medium">
								ارسال
							</button>

							<button
								onClick={handleEditCancel}
								className="px-4 py-2 bg-white hover:bg-gray-100 text-gray-600 text-sm rounded-full border border-gray-200 transition-colors duration-150 font-medium">
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
                            ${isUser ? "bg-[#fff6d9] text-gray-900" : "text-gray-900"}`}>
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
