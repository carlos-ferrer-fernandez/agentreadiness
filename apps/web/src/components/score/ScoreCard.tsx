import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn, getGradeColor, getScoreInterpretation } from '@/lib/utils'

interface ScoreCardProps {
  score: number
  grade: string
  trend?: number
  percentile?: number
  components?: Record<string, number>
  size?: 'sm' | 'md' | 'lg' | 'xl'
  animate?: boolean
  onClick?: () => void
  className?: string
}

const sizeConfig = {
  sm: { width: 80, scoreSize: 'text-2xl', gradeSize: 'text-lg' },
  md: { width: 120, scoreSize: 'text-4xl', gradeSize: 'text-2xl' },
  lg: { width: 180, scoreSize: 'text-6xl', gradeSize: 'text-4xl' },
  xl: { width: 240, scoreSize: 'text-7xl', gradeSize: 'text-5xl' },
}

export function ScoreCard({
  score,
  grade,
  trend = 0,
  percentile,
  components,
  size = 'md',
  animate = true,
  onClick,
  className,
}: ScoreCardProps) {
  const config = sizeConfig[size]
  const color = getGradeColor(grade)
  const interpretation = getScoreInterpretation(grade)
  
  // Calculate stroke dash for circular progress
  const radius = (config.width - 12) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (score / 100) * circumference

  return (
    <motion.div
      className={cn(
        "flex flex-col items-center",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
      whileHover={onClick ? { scale: 1.02 } : undefined}
      whileTap={onClick ? { scale: 0.98 } : undefined}
    >
      <div style={{ width: config.width, height: config.width }} className="relative">
        {/* Background circle */}
        <svg
          width={config.width}
          height={config.width}
          className="transform -rotate-90"
        >
          <circle
            cx={config.width / 2}
            cy={config.width / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={8}
          />
          <motion.circle
            cx={config.width / 2}
            cy={config.width / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={8}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={animate ? { strokeDashoffset: circumference } : false}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>
        
        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={animate ? { opacity: 0, scale: 0.5 } : false}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3, duration: 0.3 }}
            className={cn("font-bold", config.scoreSize)}
            style={{ color }}
          >
            {score}
          </motion.span>
        </div>
      </div>

      {/* Grade */}
      <motion.div
        initial={animate ? { opacity: 0, y: 10 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.3 }}
        className={cn("mt-2 font-bold", config.gradeSize)}
        style={{ color }}
      >
        {grade}
      </motion.div>

      {/* Interpretation */}
      <motion.p
        initial={animate ? { opacity: 0 } : false}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.3 }}
        className="text-xs text-muted-foreground text-center mt-1 max-w-[200px]"
      >
        {interpretation}
      </motion.p>

      {/* Trend indicator */}
      {trend !== 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className={cn(
            "flex items-center gap-1 text-sm mt-2",
            trend > 0 ? 'text-green-600' : 'text-red-600'
          )}
        >
          {trend > 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>{trend > 0 ? '+' : ''}{trend} pts</span>
        </motion.div>
      )}
      
      {trend === 0 && (
        <div className="flex items-center gap-1 text-sm mt-2 text-gray-500">
          <Minus size={14} />
          <span>No change</span>
        </div>
      )}

      {/* Percentile */}
      {percentile !== undefined && (
        <div className="text-xs text-muted-foreground mt-1">
          Top {100 - percentile}% of docs
        </div>
      )}

      {/* Component breakdown */}
      {components && size !== 'sm' && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          transition={{ delay: 0.6, duration: 0.3 }}
          className="mt-4 w-full space-y-2"
        >
          <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Component Breakdown
          </div>
          {Object.entries(components).map(([key, value], index) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-xs w-24 capitalize">{key.replace(/_/g, ' ')}</span>
              <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${value}%` }}
                  transition={{ delay: 0.7 + index * 0.1, duration: 0.5 }}
                  className="h-full rounded-full"
                  style={{ backgroundColor: color }}
                />
              </div>
              <span className="text-xs w-8 text-right">{value}%</span>
            </div>
          ))}
        </motion.div>
      )}
    </motion.div>
  )
}
