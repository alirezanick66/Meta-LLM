import axios from "axios"

// ساخت instance از axios با تنظیمات پایه
const api = axios.create({
	baseURL: "/api", // به خاطر proxy در vite.config
	timeout: 30000, // 30 ثانیه
	headers: {
		"Content-Type": "application/json",
	},
})

// Interceptor برای لاگ کردن requests (فقط در dev)
if (import.meta.env.DEV) {
	api.interceptors.request.use(
		(config) => {
			console.log(
				"🚀 API Request:",
				config.method.toUpperCase(),
				config.url,
			)
			return config
		},
		(error) => {
			console.error("❌ Request Error:", error)
			return Promise.reject(error)
		},
	)

	api.interceptors.response.use(
		(response) => {
			console.log(
				"✅ API Response:",
				response.status,
				response.config.url,
			)
			return response
		},
		(error) => {
			console.error(
				"❌ Response Error:",
				error.response?.status,
				error.message,
			)
			return Promise.reject(error)
		},
	)
}

/**
 * ارسال سوال به API (با پشتیبانی از AbortController)
 *
 * @param {string} query - سوال کاربر
 * @param {number} temperature - میزان خلاقیت (0-2)
 * @param {AbortSignal} signal - برای cancel کردن request
 * @returns {Promise} - پاسخ API
 */
export const sendMessage = async (query, temperature = 0.3, signal = null) => {
	try {
		const config = {
			signal, // ✅ اضافه کردن signal برای cancel
		}

		const response = await api.post(
			"/chat",
			{
				query,
				temperature,
			},
			signal ? config : {}, // ✅ ‫فقط اگه signal داریم config رو pass کن
		)
		return response.data
	} catch (error) {
		// چک کردن اینکه request cancel شده یا نه
		if (axios.isCancel(error)) {
			console.log("Request canceled:", error.message)
			throw { message: "Request canceled", name: "CanceledError" }
		}

		// مدیریت خطاهای دیگه
		if (error.response) {
			// سرور پاسخ داده ولی با error
			throw {
				message:
					error.response.data.error || "خطا در دریافت پاسخ از سرور",
				status: error.response.status,
			}
		} else if (error.request) {
			// درخواست فرستاده شده ولی پاسخی نیومده
			throw {
				message:
					"سرور پاسخگو نیست. لطفاً اتصال اینترنت خود را بررسی کنید.",
				status: 0,
			}
		} else {
			// خطای دیگه
			throw {
				message: error.message || "خطای نامشخص رخ داده است",
				status: -1,
			}
		}
	}
}

/**
 * بررسی وضعیت سلامت سرور
 * @returns {Promise} - وضعیت health
 */
export const checkHealth = async () => {
	try {
		const response = await api.get("/health")
		return response.data
	} catch (error) {
		console.error("Health check failed:", error)
		throw error
	}
}
/**
 * ‫ارسال سوال با SSE — دریافت وضعیت pipeline در real-time
 *
 * @param {string} query - سوال کاربر
 * @param {number} temperature - میزان خلاقیت
 * @param {function} onStatus - callback برای وضعیت pipeline
 * @param {function} onDone - callback برای پاسخ نهایی
 * @param {function} onError - callback برای خطا
 * @param {AbortSignal} signal - برای cancel کردن
 */
export const sendMessageStream = async (
	query,
	temperature = 0.3,
	onStatus,
	onDone,
	onError,
	signal = null,
) => {
	try {
		const response = await fetch("/api/chat/stream", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ query, temperature }),
			signal,
		})

		if (!response.ok) {
			throw new Error(`HTTP error: ${response.status}`)
		}

		const reader = response.body.getReader()
		const decoder = new TextDecoder()
		let buffer = ""

		while (true) {
			const { done, value } = await reader.read()
			if (done) break

			buffer += decoder.decode(value, { stream: true })

			// ‫پردازش خط به خط
			const lines = buffer.split("\n")
			buffer = lines.pop() || ""

			let currentEvent = null

			for (const line of lines) {
				if (line.startsWith("event: ")) {
					currentEvent = line.slice(7).trim()
				} else if (line.startsWith("data: ")) {
					try {
						const data = JSON.parse(line.slice(6))

						if (currentEvent === "status") {
							onStatus?.(data.message)
						} else if (currentEvent === "done") {
							onDone?.(data)
						} else if (currentEvent === "error") {
							onError?.(new Error(data.message))
						}
					} catch (e) {
						console.error("❌ SSE parse error:", e)
					}
					currentEvent = null
				}
			}
		}
	} catch (err) {
		if (err.name === "AbortError") {
			throw { message: "Request canceled", name: "CanceledError" }
		}
		onError?.(err)
	}
}
export default api
