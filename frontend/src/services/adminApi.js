import api from "./api"

/**
 * دریافت آمار سیستم
 */
export const fetchStats = async () => {
	const res = await api.get("/stats")
	return res.data
}

/**
 * دریافت لیست اسناد
 */
export const fetchDocuments = async () => {
	const res = await api.get("/documents")
	return res.data
}

/**
 * حذف یک سند
 */
export const deleteDocument = async (id) => {
	const res = await api.delete(`/documents/${id}`)
	return res.data
}

/**
 * حذف چند سند به صورت همزمان
 */
export const deleteDocuments = async (ids) => {
	const res = await api.post("/documents/bulk-delete", { ids })
	return res.data
}

/**
 * آپلود فایل با progress
 */
export const uploadDocument = async (file, onProgress) => {
	const formData = new FormData()
	formData.append("file", file)

	const res = await api.post("/documents/upload", formData, {
		headers: { "Content-Type": "multipart/form-data" },
		onUploadProgress: (e) => {
			const percent = Math.round((e.loaded * 100) / e.total)
			onProgress?.(percent)
		},
	})
	return res.data
}

/**
 * Index کل پوشه
 */
export const indexFolder = async () => {
	const res = await api.post(
		"/documents/index-folder",
		{},
		{
			timeout: 0, // بدون timeout برای عملیات سنگین
		},
	)
	return res.data
}
