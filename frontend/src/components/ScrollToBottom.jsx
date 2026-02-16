import React from "react"

/**
 * دکمه اسکرول به پایین (نسخه بهبود یافته)
 *
 * بهبودها:
 * - Smooth transition برای fade in/out
 * - بهبود z-index برای جلوگیری از تداخل
 * - aria-label برای accessibility
 */
const ScrollToBottom = ({ onClick, show }) => {
	return (
		<button
			onClick={onClick}
			className={`fixed bottom-24 left-1/2 -translate-x-1/2 
				bg-white border-2 border-gray-300 hover:border-gray-400 
				rounded-full p-3 shadow-lg hover:shadow-xl 
				transform hover:scale-110 active:scale-95
				z-40
				transition-all duration-300
				${
					show
						? "opacity-100 translate-y-0"
						: "opacity-0 translate-y-4 pointer-events-none"
				}`}
			aria-label="اسکرول به پایین"
			aria-hidden={!show}
		>
			<svg
				className="w-5 h-5 text-gray-600"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				aria-hidden="true"
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
