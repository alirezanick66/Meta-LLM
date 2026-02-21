import React, { useState } from "react"
import SourceModal from "./SourceModal"

/**
 * نمایش منابع زیر پیام ربات — قابل collapse با modal
 */
const SourceCards = ({ sources }) => {
	const [isOpen, setIsOpen] = useState(false)
	const [selectedSource, setSelectedSource] = useState(null)

	if (!sources?.length) return null

	return (
		<>
			<div className="mt-3 w-full max-w-[85%]">
				{/* Toggle Button */}
				<button
					onClick={() => setIsOpen((prev) => !prev)}
					className="flex items-center gap-2 text-xs text-gray-400 
                        hover:text-gray-600 transition-colors duration-200 group">
					<span
						className={`transition-transform duration-200 
                        ${isOpen ? "rotate-90" : "rotate-0"}`}>
						▶
					</span>
					<span>📚 منابع ({sources.length})</span>
				</button>

				{/* Cards */}
				{isOpen && (
					<div className="mt-2 flex flex-col gap-2 animate-fadeIn">
						{sources.map((source, i) => (
							<button
								key={i}
								onClick={() => setSelectedSource(source)}
								className="text-right px-3 py-2.5 rounded-xl border border-gray-100 
                                    bg-gray-50 hover:bg-gray-100 hover:border-gray-200
                                    transition-all duration-150 group w-full">
								<div className="flex items-center justify-between gap-2">
									{/* نام فایل */}
									<span className="text-gray-400 text-xs group-hover:text-gray-500">
										مشاهده متن ←
									</span>
									<div className="flex items-center gap-1.5 min-w-0">
										<span className="text-base flex-shrink-0">
											{source.source?.endsWith(".docx")
												? "📝"
												: "📄"}
										</span>
										<span className="text-xs font-medium text-gray-700 truncate">
											{source.source || "سند نامشخص"}
										</span>
									</div>
								</div>

								{/* پیش‌نمایش متن */}
								{source.content && (
									<p className="text-xs text-gray-400 mt-1.5 line-clamp-2 text-right leading-relaxed">
										{source.content}
									</p>
								)}
							</button>
						))}
					</div>
				)}
			</div>

			{/* Modal */}
			{selectedSource && (
				<SourceModal
					source={selectedSource}
					onClose={() => setSelectedSource(null)}
				/>
			)}
		</>
	)
}

export default SourceCards
