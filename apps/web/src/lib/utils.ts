import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatNumber(num: number, decimals: number = 0): string {
  return num.toFixed(decimals)
}

export function formatPercent(num: number): string {
  return `${Math.round(num * 100)}%`
}

export function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    'A+': '#15803d',
    'A': '#16a34a',
    'A-': '#22c55e',
    'B+': '#65a30d',
    'B': '#84cc16',
    'B-': '#a3e635',
    'C+': '#ca8a04',
    'C': '#eab308',
    'C-': '#facc15',
    'D': '#f97316',
    'F': '#ef4444',
  }
  return colors[grade] || '#6b7280'
}

export function scoreToGrade(score: number): string {
  if (score >= 97) return 'A+'
  if (score >= 93) return 'A'
  if (score >= 90) return 'A-'
  if (score >= 87) return 'B+'
  if (score >= 83) return 'B'
  if (score >= 80) return 'B-'
  if (score >= 77) return 'C+'
  if (score >= 73) return 'C'
  if (score >= 70) return 'C-'
  if (score >= 60) return 'D'
  return 'F'
}

export function getScoreInterpretation(grade: string): string {
  const interpretations: Record<string, string> = {
    'A+': 'Exceptional: best-in-class agent experience',
    'A': 'Excellent: strong competitive position',
    'A-': 'Very good: minor optimization opportunities',
    'B+': 'Good: some gaps relative to leaders',
    'B': 'Above average: meaningful improvement potential',
    'B-': 'Average: significant optimization needed',
    'C+': 'Below average: competitive disadvantage risk',
    'C': 'Concerning: likely losing agent recommendations',
    'C-': 'Poor: urgent improvement required',
    'D': 'Critical: effectively invisible to agents',
    'F': 'Failing: complete restructuring needed',
  }
  return interpretations[grade] || 'Unknown'
}
