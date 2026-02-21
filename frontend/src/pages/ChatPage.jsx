import React from "react"
import { useNavigate } from "react-router-dom"
import ChatInterface from "../components/ChatInterface"

/**
 * صفحه چت — wrapper برای ChatInterface با دکمه مخفی Admin
 */
const ChatPage = () => {
	const navigate = useNavigate()
	let clickCount = 0
	let clickTimer = null

	// کلیک ۵ بار روی لوگو → رفتن به admin
	const handleLogoClick = () => {
		clickCount++
		clearTimeout(clickTimer)
		clickTimer = setTimeout(() => {
			clickCount = 0
		}, 2000)
		if (clickCount >= 5) {
			clickCount = 0
			navigate("/admin")
		}
	}

	return (
		<div className="relative">
			{/* دکمه مخفی — overlay روی لوگو در empty state */}
			<div
				onClick={handleLogoClick}
				className="fixed top-0 left-0 w-16 h-16 z-50 cursor-default"
				title=""
			/>
			<ChatInterface />
		</div>
	)
}

export default ChatPage
