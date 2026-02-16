import React from "react"

/**
 * دکمه اسکرول به پایین (وقتی کاربر بالا رفته)
 */
const ScrollToBottom = ({ onClick, show }) => {
	if (!show) return null

	return (
		<button
			onClick={onClick}
			className="fixed bottom-24 left-1/2 -translate-x-1/2 
				bg-white border-2 border-gray-300 hover:border-gray-400 
				rounded-full p-3 shadow-lg hover:shadow-xl 
				transition-all transform hover:scale-110 active:scale-95
				z-50"
			aria-label="اسکرول به پایین"
		>
			<svg
				className="w-5 h-5 text-gray-600"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					strokeLinecap="round"
					strokeLinejoin="round"
					strokeWidth={2}
					d="M19 14l-7 7m0 0l-7-7m7 7V3"
				/>
			</svg>
		</button>
	)
}

export default ScrollToBottom
