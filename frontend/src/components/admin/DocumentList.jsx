import React, { useState } from "react"
import { deleteDocument, deleteDocuments } from "../../services/adminApi"

const formatDate = (iso) => {
	if (!iso) return "—"
	return new Date(iso).toLocaleDateString("fa-IR", {
		year: "numeric",
		month: "long",
		day: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	})
}

const formatSize = (bytes) => {
	if (!bytes) return "—"
	if (bytes < 1024) return `${bytes} B`
	if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
	return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const DocumentList = ({ documents, loading, onRefresh }) => {
	const [selected, setSelected] = useState(new Set())
	const [deleting, setDeleting] = useState(false)

	const toggleSelect = (id) => {
		setSelected((prev) => {
			const next = new Set(prev)
			next.has(id) ? next.delete(id) : next.add(id)
			return next
		})
	}

	const toggleAll = () => {
		setSelected((prev) =>
			prev.size === documents.length
				? new Set()
				: new Set(documents.map((d) => d.id)),
		)
	}

	const handleDelete = async (ids) => {
		if (!confirm(`حذف ${ids.length} سند؟`)) return
		setDeleting(true)
		try {
			if (ids.length === 1) {
				await deleteDocument(ids[0])
			} else {
				await deleteDocuments(ids)
			}
			setSelected(new Set())
			onRefresh()
		} catch (err) {
			alert("خطا در حذف: " + (err.response?.data?.detail || err.message))
		} finally {
			setDeleting(false)
		}
	}

	if (loading) {
		return (
			<div className="space-y-3">
				{[...Array(3)].map((_, i) => (
					<div
						key={i}
						className="h-16 bg-gray-100 rounded-xl animate-pulse"
					/>
				))}
			</div>
		)
	}

	if (!documents.length) {
		return (
			<div className="text-center py-16 text-gray-400">
				<div className="text-5xl mb-3">📭</div>
				<p>هیچ سندی ایندکس نشده</p>
			</div>
		)
	}

	return (
		<div className="space-y-3">
			{/* Toolbar */}
			<div className="flex items-center justify-between">
				<div className="flex items-center gap-3">
					<input
						type="checkbox"
						checked={selected.size === documents.length}
						onChange={toggleAll}
						className="w-4 h-4 accent-green-500"
					/>
					<span className="text-sm text-gray-500">
						{selected.size > 0
							? `${selected.size} سند انتخاب شده`
							: `${documents.length} سند`}
					</span>
				</div>

				{selected.size > 0 && (
					<button
						onClick={() => handleDelete([...selected])}
						disabled={deleting}
						className="flex items-center gap-2 px-4 py-2 bg-red-50 
                            hover:bg-red-100 text-red-600 text-sm rounded-xl 
                            transition-colors duration-200 disabled:opacity-50">
						{deleting ? "⏳" : "🗑️"}
						حذف انتخاب‌شده‌ها
					</button>
				)}
			</div>

			{/* لیست */}
			{documents.map((doc) => (
				<div
					key={doc.id}
					className={`flex items-center gap-4 p-4 rounded-xl border-2 
                        transition-all duration-150 cursor-pointer
                        ${
							selected.has(doc.id)
								? "border-green-300 bg-green-50"
								: "border-gray-100 bg-white hover:border-gray-200"
						}`}
					onClick={() => toggleSelect(doc.id)}>
					<input
						type="checkbox"
						checked={selected.has(doc.id)}
						onChange={() => toggleSelect(doc.id)}
						onClick={(e) => e.stopPropagation()}
						className="w-4 h-4 accent-green-500 flex-shrink-0"
					/>

					{/* آیکون فایل */}
					<div
						className="w-10 h-10 bg-gray-100 rounded-lg flex items-center 
                        justify-center text-lg flex-shrink-0">
						{doc.filename?.endsWith(".docx") ? "📝" : "📄"}
					</div>

					{/* اطلاعات */}
					<div className="flex-1 text-right min-w-0">
						<p className="font-medium text-gray-900 truncate">
							{doc.filename}
						</p>
						<div className="flex items-center gap-3 mt-1 justify-end">
							<span className="text-xs text-gray-400">
								{doc.total_chunks} chunk
							</span>
							{doc.file_size && (
								<span className="text-xs text-gray-400">
									{formatSize(doc.file_size)}
								</span>
							)}
							<span className="text-xs text-gray-400">
								{formatDate(doc.indexed_at)}
							</span>
						</div>
						{doc.updated_at &&
							doc.updated_at !== doc.indexed_at && (
								<p className="text-xs text-blue-400 mt-0.5">
									آخرین تغییر: {formatDate(doc.updated_at)}
								</p>
							)}
					</div>

					{/* دکمه حذف تکی */}
					<button
						onClick={(e) => {
							e.stopPropagation()
							handleDelete([doc.id])
						}}
						disabled={deleting}
						className="w-8 h-8 flex items-center justify-center rounded-lg
                            text-gray-300 hover:text-red-500 hover:bg-red-50
                            transition-all duration-200 flex-shrink-0">
						🗑️
					</button>
				</div>
			))}
		</div>
	)
}

export default DocumentList
