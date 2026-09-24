/**
 * Presentation formatters and helper utilities.
 */

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'Not inspected yet';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatRiskScore(score: number): string {
  return score.toFixed(1);
}

export function getRiskLevelClass(level: string): 'high' | 'medium' | 'low' {
  switch (level.toUpperCase()) {
    case 'HIGH':
      return 'high';
    case 'MEDIUM':
      return 'medium';
    case 'LOW':
    default:
      return 'low';
  }
}
