import React, { useState, useRef, useCallback } from "react"
import { uploadDocument } from "../../services/adminApi"

const ACCEPTED = [".md", ".docx"]

const UploadZone = ({ onUploadComplete }) => {
	const [isDragging, setIsDragging] = useState(false)
	const [uploads, setUploads] = useState([]) // [{name, progress, status, error}]
	const inputRef = useRef(null)

	const processFile = useCallback(
		async (file) => {
			const ext = "." + file.name.split(".").pop().toLowerCase()
			if (!ACCEPTED.includes(ext)) {
				setUploads((prev) => [
					...prev,
					{
						name: file.name,
						progress: 0,
						status: "error",
						error: "فرمت پشتیبانی نمی‌شود",
					},
				])
				return
			}

			// اضافه کردن به لیست با وضعیت uploading
			setUploads((prev) => [
				...prev,
				{ name: file.name, progress: 0, status: "uploading" },
			])

			try {
				await uploadDocument(file, (percent) => {
					setUploads((prev) =>
						prev.map((u) =>
							u.name === file.name
								? { ...u, progress: percent }
								: u,
						),
					)
				})

				setUploads((prev) =>
					prev.map((u) =>
						u.name === file.name
							? { ...u, progress: 100, status: "done" }
							: u,
					),
				)
				onUploadComplete?.()
			} catch (err) {
				setUploads((prev) =>
					prev.map((u) =>
						u.name === file.name
							? {
									...u,
									status: "error",
									error:
										err.response?.data?.detail ||
										"خطا در آپلود",
								}
							: u,
					),
				)
			}
		},
		[onUploadComplete],
	)

	const handleDrop = useCallback(
		(e) => {
			e.preventDefault()
			setIsDragging(false)
			Array.from(e.dataTransfer.files).forEach(processFile)
		},
		[processFile],
	)

	const handleFileInput = (e) => {
		Array.from(e.target.files).forEach(processFile)
		e.target.value = ""
	}

	return (
		<div className="space-y-4">
			{/* Drop Zone */}
			<div
				onDragOver={(e) => {
					e.preventDefault()
					setIsDragging(true)
				}}
				onDragLeave={() => setIsDragging(false)}
				onDrop={handleDrop}
				onClick={() => inputRef.current?.click()}
				className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer
                    transition-all duration-200
                    ${
						isDragging
							? "border-green-400 bg-green-50 scale-[1.02]"
							: "border-gray-200 hover:border-green-300 hover:bg-gray-50"
					}`}>
				<input
					ref={inputRef}
					type="file"
					accept={ACCEPTED.join(",")}
					multiple
					onChange={handleFileInput}
					className="hidden"
				/>
				<div className="text-4xl mb-3">{isDragging ? "📂" : "☁️"}</div>
				<p className="text-gray-700 font-medium">
					{isDragging ? "رها کنید..." : "فایل را اینجا رها کنید"}
				</p>
				<p className="text-gray-400 text-sm mt-1">یا کلیک کنید</p>
				<p className="text-gray-300 text-xs mt-3">
					فرمت‌های مجاز: {ACCEPTED.join("، ")}
				</p>
			</div>

			{/* لیست آپلودها */}
			{uploads.length > 0 && (
				<div className="space-y-2">
					{uploads.map((u, i) => (
						<div
							key={i}
							className="bg-gray-50 rounded-xl px-4 py-3">
							<div className="flex items-center justify-between mb-1">
								<span className="text-xs">
									{u.status === "done"
										? "✅"
										: u.status === "error"
											? "❌"
											: "⏳"}
								</span>
								<span className="text-sm text-gray-700 font-medium">
									{u.name}
								</span>
							</div>
							{u.status === "uploading" && (
								<div className="w-full bg-gray-200 rounded-full h-1.5">
									<div
										className="bg-green-400 h-1.5 rounded-full transition-all duration-300"
										style={{ width: `${u.progress}%` }}
									/>
								</div>
							)}
							{u.status === "error" && (
								<p className="text-xs text-red-500 text-right">
									{u.error}
								</p>
							)}
							{u.status === "done" && (
								<p className="text-xs text-green-600 text-right">
									در حال پردازش...
								</p>
							)}
						</div>
					))}
					<button
						onClick={() => setUploads([])}
						className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
						پاک کردن لیست
					</button>
				</div>
			)}
		</div>
	)
}

export default UploadZone
