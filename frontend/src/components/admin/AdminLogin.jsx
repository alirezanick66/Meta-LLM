import React, { useState } from "react"

const ADMIN_PASSWORD = "admin1234" // بعداً از env بخون

const AdminLogin = ({ onLogin }) => {
	const [password, setPassword] = useState("")
	const [error, setError] = useState(false)
	const [shake, setShake] = useState(false)

	const handleSubmit = (e) => {
		e.preventDefault()
		if (password === ADMIN_PASSWORD) {
			sessionStorage.setItem("admin_auth", "true")
			onLogin()
		} else {
			setError(true)
			setShake(true)
			setTimeout(() => setShake(false), 500)
		}
	}

	return (
		<div className="min-h-screen bg-white flex items-center justify-center">
			<div
				className={`w-full max-w-sm px-8 ${shake ? "animate-shake" : ""}`}>
				{/* لوگو */}
				<div className="text-center mb-10">
					<div
						className="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 
                        rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
						<span className="text-white text-3xl font-bold">م</span>
					</div>
					<h1 className="text-2xl font-bold text-gray-900">
						پنل مدیریت
					</h1>
					<p className="text-gray-500 text-sm mt-1">
						متا — سیستم RAG
					</p>
				</div>

				<form onSubmit={handleSubmit} className="space-y-4">
					<div>
						<input
							type="password"
							value={password}
							onChange={(e) => {
								setPassword(e.target.value)
								setError(false)
							}}
							placeholder="رمز عبور"
							autoFocus
							className={`w-full px-4 py-3 rounded-xl border-2 text-right
                                bg-gray-50 focus:bg-white focus:outline-none transition-all
                                ${
									error
										? "border-red-400 focus:border-red-400"
										: "border-gray-200 focus:border-green-400"
								}`}
						/>
						{error && (
							<p className="text-red-500 text-xs mt-2 text-right">
								رمز عبور اشتباه است
							</p>
						)}
					</div>

					<button
						type="submit"
						className="w-full py-3 bg-green-500 hover:bg-green-600 
                            text-white font-medium rounded-xl transition-colors duration-200
                            active:scale-95 transform">
						ورود
					</button>
				</form>
			</div>
		</div>
	)
}

export default AdminLogin
