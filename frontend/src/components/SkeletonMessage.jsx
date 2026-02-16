import React from "react"

/**
 * Skeleton loading برای پیام در حال بارگذاری
 */
const SkeletonMessage = () => {
	return (
		<div className="w-full py-2 animate-fadeIn">
			<div className="max-w-3xl ml-auto mr-4 px-4 flex flex-col items-start">
				<div className="px-4 py-3 w-full max-w-[85%]">
					<div className="space-y-3 animate-pulse">
						{/* خط اول */}
						<div className="h-4 bg-gray-200 rounded w-3/4"></div>
						{/* خط دوم */}
						<div className="h-4 bg-gray-200 rounded w-full"></div>
						{/* خط سوم */}
						<div className="h-4 bg-gray-200 rounded w-5/6"></div>
					</div>
				</div>
			</div>
		</div>
	)
}

export default SkeletonMessage
