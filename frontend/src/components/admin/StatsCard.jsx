import React from "react"

const StatItem = ({ label, value, icon }) => (
	<div
		className="bg-white border border-gray-100 rounded-2xl p-5 shadow-sm 
        hover:shadow-md transition-shadow duration-200">
		<div className="flex items-center justify-between mb-3">
			<span className="text-2xl">{icon}</span>
			<span className="text-3xl font-bold text-gray-900">
				{value?.toLocaleString("fa-IR") ?? "—"}
			</span>
		</div>
		<p className="text-sm text-gray-500 text-right">{label}</p>
	</div>
)

const StatsCard = ({ stats, loading }) => {
	if (loading) {
		return (
			<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
				{[...Array(4)].map((_, i) => (
					<div
						key={i}
						className="bg-gray-100 rounded-2xl p-5 h-28 animate-pulse"
					/>
				))}
			</div>
		)
	}

	return (
		<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
			<StatItem
				icon="📄"
				label="اسناد ایندکس‌شده"
				value={stats?.total_documents}
			/>
			<StatItem
				icon="🧩"
				label="تعداد Chunks"
				value={stats?.total_chunks}
			/>
			<StatItem
				icon="🔍"
				label="وکتورهای Qdrant"
				value={stats?.qdrant_vectors}
			/>
			<StatItem
				icon="📚"
				label="BM25 Chunks"
				value={stats?.bm25_chunks}
			/>
		</div>
	)
}

export default StatsCard
