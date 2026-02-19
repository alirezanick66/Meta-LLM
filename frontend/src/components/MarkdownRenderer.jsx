import React, { useCallback } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { useState } from "react"

// 🎯 کامپوننت CodeBlock
const CodeBlock = ({ inline, className, children }) => {
	const [copied, setCopied] = useState(false)
	const language = /language-(\w+)/.exec(className || "")?.[1]

	const handleCopy = useCallback(async () => {
		try {
			await navigator.clipboard.writeText(String(children))
			setCopied(true)
			setTimeout(() => setCopied(false), 2000)
		} catch (err) {
			console.error("Copy failed:", err)
		}
	}, [children])

	if (inline) {
		return (
			<code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono">
				{children}
			</code>
		)
	}

	return (
		<div className="relative group my-3">
			{language && (
				<div className="absolute top-2 right-2 bg-gray-700 text-gray-300 text-xs px-2 py-1 rounded">
					{language}
				</div>
			)}
			<button
				onClick={handleCopy}
				className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 bg-gray-700 hover:bg-gray-600 text-white text-xs px-2 py-1 rounded transition-opacity duration-200 flex items-center gap-1"
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
				<code className="font-mono text-sm leading-relaxed">
					{children}
				</code>
			</pre>
		</div>
	)
}

// 🎯 کامپوننت‌های Markdown
const components = {
	strong: ({ node, ...props }) => (
		<strong className="font-bold text-gray-900" {...props} />
	),
	em: ({ node, ...props }) => (
		<em className="italic text-gray-700" {...props} />
	),
	del: ({ node, ...props }) => (
		<del className="line-through text-gray-500" {...props} />
	),
	p: ({ node, ...props }) => <p className="my-1.5 leading-7" {...props} />,
	h1: ({ node, ...props }) => (
		<h1 className="text-2xl font-bold mt-4 mb-2 text-gray-900" {...props} />
	),
	h2: ({ node, ...props }) => (
		<h2 className="text-xl font-bold mt-3 mb-2 text-gray-900" {...props} />
	),
	h3: ({ node, ...props }) => (
		<h3 className="text-lg font-bold mt-2 mb-1 text-gray-900" {...props} />
	),
	a: ({ node, ...props }) => (
		<a
			className="text-blue-600 hover:text-blue-800 hover:underline"
			target="_blank"
			rel="noopener noreferrer"
			{...props}
		/>
	),
	blockquote: ({ node, ...props }) => (
		<blockquote
			className="border-r-4 border-gray-300 pr-4 my-2 text-gray-700 italic"
			{...props}
		/>
	),
	hr: ({ node, ...props }) => (
		<hr className="my-4 border-gray-300" {...props} />
	),
	ul: ({ node, ...props }) => (
		<ul className="list-disc list-inside my-2 space-y-1 mr-4" {...props} />
	),
	ol: ({ node, ...props }) => (
		<ol
			className="list-decimal list-inside my-2 space-y-1 mr-4"
			{...props}
		/>
	),
	li: ({ node, ...props }) => (
		<li className="text-gray-800 leading-relaxed" {...props} />
	),
	table: ({ node, ...props }) => (
		<div className="overflow-x-auto my-4">
			<table
				className="min-w-full border-collapse border-2 border-gray-400"
				{...props}
			/>
		</div>
	),
	thead: ({ node, ...props }) => <thead className="bg-gray-200" {...props} />,
	tbody: ({ node, ...props }) => <tbody className="bg-white" {...props} />,
	tr: ({ node, ...props }) => (
		<tr className="hover:bg-gray-50 transition-colors" {...props} />
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
	code: CodeBlock,
}

// 🎯 کامپوننت اصلی
const MarkdownRenderer = ({ content, isInline = false }) => {
	const renderComponents = isInline
		? { ...components, p: ({ node, ...props }) => <span {...props} /> }
		: components

	return (
		<ReactMarkdown
			remarkPlugins={[remarkGfm]}
			components={renderComponents}>
			{content}
		</ReactMarkdown>
	)
}

export default React.memo(MarkdownRenderer)
