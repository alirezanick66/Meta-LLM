import { useState, useEffect } from "react"

/**
 * Hook برای انیمیشن تایپ کاراکتر به کاراکتر
 * @param {string} text - متن کامل
 * @param {number} speed - سرعت تایپ (میلی‌ثانیه)
 * @param {boolean} enabled - فعال/غیرفعال بودن افکت
 */
export const useTypingEffect = (text, speed = 20, enabled = true) => {
	const [displayedText, setDisplayedText] = useState("")
	const [isTyping, setIsTyping] = useState(false)

	useEffect(() => {
		if (!enabled || !text) {
			setDisplayedText(text)
			return
		}

		setIsTyping(true)
		setDisplayedText("")

		let index = 0
		const timer = setInterval(() => {
			if (index < text.length) {
				setDisplayedText((prev) => prev + text[index])
				index++
			} else {
				clearInterval(timer)
				setIsTyping(false)
			}
		}, speed)

		return () => {
			clearInterval(timer)
			setIsTyping(false)
		}
	}, [text, speed, enabled])

	return { displayedText, isTyping }
}
