import { useState, useEffect, useRef } from "react"

/**
 * Hook مدیریت وضعیت typing
 * فقط یه delay کوتاه بعد از نمایش پیام — animation کامل به CSS سپرده شده
 */
export const useTypingEffect = (text, speed = 20, enabled = true) => {
	const [isTyping, setIsTyping] = useState(false)
	const timerRef = useRef(null)

	useEffect(() => {
		if (!enabled || !text) {
			setIsTyping(false)
			return
		}

		setIsTyping(true)

		// ‫delay متناسب با طول متن — حداکثر 2 ثانیه
		const delay = Math.min(text.length * 10, 2000)

		timerRef.current = setTimeout(() => {
			setIsTyping(false)
		}, delay)

		return () => {
			if (timerRef.current) clearTimeout(timerRef.current)
		}
	}, [text, enabled])

	return { displayedText: text, isTyping }
}
