import React, { useState, useEffect, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import AdminLogin from "../components/admin/AdminLogin"
import StatsCard from "../components/admin/StatsCard"
import DocumentList from "../components/admin/DocumentList"
import UploadZone from "../components/admin/UploadZone"
import { fetchStats, fetchDocuments, indexFolder } from "../services/adminApi"

const AdminPage = () => {
	const navigate = useNavigate()
	const [isAuth, setIsAuth] = useState(
		sessionStorage.getItem("admin_auth") === "true",
	)
	const [stats, setStats] = useState(null)
	const [documents, setDocuments] = useState([])
	const [statsLoading, setStatsLoading] = useState(true)
	const [docsLoading, setDocsLoading] = useState(true)
	const [indexing, setIndexing] = useState(false)
	const [activeTab, setActiveTab] = useState("documents") // 'documents' | 'upload'

	const loadData = useCallback(async () => {
		try {
			setStatsLoading(true)
			setDocsLoading(true)
			const [s, d] = await Promise.all([fetchStats(), fetchDocuments()])
			setStats(s)
			setDocuments(d.documents || [])
		} catch (err) {
			console.error("خطا در لود داده:", err)
		} finally {
			setStatsLoading(false)
			setDocsLoading(false)
		}
	}, [])

	useEffect(() => {
		if (isAuth) loadData()
	}, [isAuth, loadData])

	const handleIndexFolder = async () => {
		if (!confirm("ایندکس کل پوشه documents؟")) return
		setIndexing(true)
		try {
			const result = await indexFolder()
			alert(
				`✅ پردازش تمام شد:\nموفق: ${result.succeeded}\nجایگزین: ${result.replaced}\nSkip: ${result.skipped}\nخطا: ${result.failed}`,
			)
			loadData()
		} catch (err) {
			alert("خطا: " + err.message)
		} finally {
			setIndexing(false)
		}
	}

	const handleLogout = () => {
		sessionStorage.removeItem("admin_auth")
		setIsAuth(false)
	}

	if (!isAuth) {
		return <AdminLogin onLogin={() => setIsAuth(true)} />
	}

	return (
		<div className="min-h-screen bg-gray-50">
			{/* Header */}
			<header className="bg-white border-b border-gray-100 sticky top-0 z-10">
				<div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
					<div className="flex items-center gap-4">
						<button
							onClick={() => navigate("/")}
							className="text-gray-400 hover:text-gray-600 transition-colors text-sm flex items-center gap-1">
							← بازگشت به چت
						</button>
						<div className="h-4 w-px bg-gray-200" />
						<div className="flex items-center gap-2">
							<div
								className="w-7 h-7 bg-gradient-to-br from-green-400 to-green-600 
                                rounded-lg flex items-center justify-center">
								<span className="text-white text-sm font-bold">
									م
								</span>
							</div>
							<span className="font-bold text-gray-900">
								پنل مدیریت
							</span>
						</div>
					</div>

					<div className="flex items-center gap-3">
						<button
							onClick={handleIndexFolder}
							disabled={indexing}
							className="flex items-center gap-2 px-4 py-2 bg-green-50 
                                hover:bg-green-100 text-green-700 text-sm rounded-xl 
                                transition-colors disabled:opacity-50">
							{indexing ? "⏳ در حال پردازش..." : "🔄 Index پوشه"}
						</button>
						<button
							onClick={loadData}
							className="w-9 h-9 flex items-center justify-center rounded-xl
                                bg-gray-100 hover:bg-gray-200 transition-colors text-gray-600"
							title="رفرش">
							↻
						</button>
						<button
							onClick={handleLogout}
							className="text-sm text-gray-400 hover:text-red-500 transition-colors">
							خروج
						</button>
					</div>
				</div>
			</header>

			<main className="max-w-5xl mx-auto px-6 py-8 space-y-8">
				{/* Stats */}
				<section>
					<h2 className="text-sm font-medium text-gray-500 mb-4 text-right">
						آمار سیستم
					</h2>
					<StatsCard stats={stats} loading={statsLoading} />
				</section>

				{/* Tabs */}
				<section>
					<div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit mr-auto">
						{[
							{ key: "documents", label: "📄 اسناد" },
							{ key: "upload", label: "⬆️ آپلود" },
						].map((tab) => (
							<button
								key={tab.key}
								onClick={() => setActiveTab(tab.key)}
								className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200
                                    ${
										activeTab === tab.key
											? "bg-white text-gray-900 shadow-sm"
											: "text-gray-500 hover:text-gray-700"
									}`}>
								{tab.label}
							</button>
						))}
					</div>

					<div className="mt-4">
						{activeTab === "documents" ? (
							<DocumentList
								documents={documents}
								loading={docsLoading}
								onRefresh={loadData}
							/>
						) : (
							<UploadZone onUploadComplete={loadData} />
						)}
					</div>
				</section>
			</main>
		</div>
	)
}

export default AdminPage
