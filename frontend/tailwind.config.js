/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
	darkMode: "class",
	theme: {
		extend: {
			colors: {
				primary: {
					bg: "#f9fafb", // خاکستری بسیار روشن برای پس‌زمینه کلی
					secondary: "#ffffff", // سفید برای هدر و کانتینرها
					accent: "#10a37f", // سبز اصلی (همان رنگ قبلی)
				},
				user: {
					bg: "#10a37f", // پیام کاربر سبز می‌ماند
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
