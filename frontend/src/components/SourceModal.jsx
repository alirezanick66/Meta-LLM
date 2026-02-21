import React, { useEffect } from "react"

/**
 * Modal نمایش متن کامل chunk
 */
const SourceModal = ({ source, onClose }) => {
	// بستن با ESC
	useEffect(() => {
		const handleKey = (e) => {
			if (e.key === "Escape") onClose()
		}
		document.addEventListener("keydown", handleKey)
		return () => document.removeEventListener("keydown", handleKey)
	}, [onClose])

	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center p-4
                bg-black/40 backdrop-blur-sm animate-fadeIn"
			onClick={onClose}>
			<div
				className="bg-white rounded-2xl shadow-2xl w-full max-w-lg 
                    max-h-[80vh] flex flex-col animate-fadeIn"
				onClick={(e) => e.stopPropagation()}>
				{/* Header */}
				<div
					className="flex items-center justify-between px-5 py-4 
                    border-b border-gray-100">
					<button
						onClick={onClose}
						className="w-8 h-8 flex items-center justify-center rounded-full
                            text-gray-400 hover:text-gray-600 hover:bg-gray-100
                            transition-all duration-200">
						✕
					</button>
					<div className="flex items-center gap-2">
						<span>
							{source.source?.endsWith(".docx") ? "📝" : "📄"}
						</span>
						<span className="font-medium text-gray-900 text-sm">
							{source.source || "سند نامشخص"}
						</span>
					</div>
				</div>

				{/* متن chunk */}
				<div className="flex-1 overflow-y-auto px-5 py-4 custom-scrollbar">
					<p className="text-sm text-gray-700 leading-8 text-right whitespace-pre-wrap">
						{source.content || "متنی موجود نیست"}
					</p>
				</div>
			</div>
		</div>
	)
}

export default SourceModal
