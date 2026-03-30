import React from "react"

/**
 * ‫Skeleton loading با نمایش وضعیت pipeline
 */
const SkeletonMessage = ({ status }) => {
	return (
		<div className="w-full py-2 animate-fadeIn">
			<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
				<div className="px-4 py-3 w-full max-w-[85%]">
					{/* ‫نمایش وضعیت فعلی pipeline */}
					{status && (
						<div className="flex items-center gap-2 mb-3 animate-fadeIn">
							<span className="text-sm text-gray-500">
								{status}
							</span>
							<span className="flex gap-1">
								<span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-typing"></span>
								<span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-typing-delay-1"></span>
								<span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-typing-delay-2"></span>
							</span>
						</div>
					)}

					{/* ‫skeleton bars */}
					<div className="space-y-3 animate-pulse">
						<div className="h-4 bg-gray-200 rounded w-3/4"></div>
						<div className="h-4 bg-gray-200 rounded w-full"></div>
						<div className="h-4 bg-gray-200 rounded w-5/6"></div>
					</div>
				</div>
			</div>
		</div>
	)
}

export default SkeletonMessage
