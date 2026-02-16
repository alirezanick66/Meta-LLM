import { useState, useEffect } from "react"

/**
 * Hook برای انیمیشن تایپ کاراکتر به کاراکتر (نسخه اصلاح شده)
 * @param {string} text - متن کامل
 * @param {number} speed - سرعت تایپ (میلی‌ثانیه)
 * @param {boolean} enabled - فعال/غیرفعال بودن افکت
 */
export const useTypingEffect = (text, speed = 20, enabled = true) => {
	const [displayedText, setDisplayedText] = useState("")
	const [isTyping, setIsTyping] = useState(false)

	useEffect(() => {
		// اگه افکت غیرفعاله یا متن خالیه، کل متن رو نشون بده
		if (!enabled || !text) {
			setDisplayedText(text || "")
			setIsTyping(false)
			return
		}

		// ریست کردن
		setIsTyping(true)
		setDisplayedText("")

		let index = 0
		const timer = setInterval(() => {
			// ✅ اول چک می‌کنیم که index از طول متن کمتر باشه
			if (index < text.length) {
				// ✅ کاراکتر فعلی رو اضافه می‌کنیم
				setDisplayedText(text.substring(0, index + 1))
				index++
			} else {
				// ✅ تایپ تموم شد
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
