/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
	darkMode: "class",
	theme: {
		extend: {
			colors: {
				primary: {
					bg: "#ffffff", // سفید کامل برای پس‌زمینه (مثل پیام ربات)
					secondary: "#ffffff", // سفید برای هدر و کانتینرها
					accent: "#10a37f", // سبز اصلی
				},
				user: {
					bg: "#fff6d9", // پیام کاربر زرد
				},
				bot: {
					bg: "#ffffff", // پیام ربات سفید
				},
			},
			fontFamily: {
				sans: ["mikhak", "sans-serif"],
			},
		},
	},
	plugins: [],
}
