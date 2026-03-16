import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn, scoreToGrade, getGradeColor } from '@/lib/utils'

interface ScoreDataPoint {
  date: string
  score: number
  grade: string
}

interface ScoreTrendProps {
  data: ScoreDataPoint[]
  className?: string
}

export function ScoreTrend({ data, className }: ScoreTrendProps) {
  const chartData = useMemo(() => {
    return data.map(d => ({
      ...d,
      date: new Date(d.date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      }),
    }))
  }, [data])

  const currentScore = data[data.length - 1]?.score || 0
  const previousScore = data[data.length - 2]?.score || currentScore
  const trend = currentScore - previousScore

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const score = payload[0].value
      const grade = scoreToGrade(score)
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-lg font-bold" style={{ color: getGradeColor(grade) }}>
            {score} ({grade})
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-medium flex items-center justify-between">
          <span>Score Trend</span>
          <span className={cn(
            "text-sm",
            trend > 0 ? "text-green-600" : trend < 0 ? "text-red-600" : "text-gray-500"
          )}>
            {trend > 0 ? '+' : ''}{trend} pts
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${value}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={90} stroke="#22c55e" strokeDasharray="3 3" />
              <ReferenceLine y={80} stroke="#84cc16" strokeDasharray="3 3" />
              <ReferenceLine y={70} stroke="#eab308" strokeDasharray="3 3" />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#3b82f6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-between mt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-green-500" />
            <span>A (90+)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-lime-500" />
            <span>B (80+)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-0.5 bg-yellow-500" />
            <span>C (70+)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
