import type { Job } from '../types'

const statusColors: Record<string, string> = {
  queued: 'var(--text-muted)',
  pending: 'var(--warning)',
  running: 'var(--accent)',
  succeeded: 'var(--success)',
  failed: 'var(--danger)',
  cancelled: 'var(--text-muted)',
}

export function JobList({
  jobs,
  selected,
  onSelect,
}: {
  jobs: Job[]
  selected: string | null
  onSelect: (id: string) => void
}) {
  return (
    <ul style={{ listStyle: 'none', margin: 0, padding: '0.5rem' }}>
      {jobs.length === 0 && (
        <li style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          No jobs yet. Submit via POST /api/v1/jobs
        </li>
      )}
      {jobs.map((j) => (
        <li
          key={j.id}
          onClick={() => onSelect(j.id)}
          style={{
            padding: '0.75rem 1rem',
            marginBottom: 4,
            borderRadius: 8,
            cursor: 'pointer',
            background: selected === j.id ? 'var(--bg-elevated)' : 'transparent',
            borderLeft: selected === j.id ? '3px solid var(--accent)' : '3px solid transparent',
          }}
        >
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{j.id.slice(0, 8)}</div>
          <div
            style={{
              fontSize: '0.75rem',
              marginTop: 4,
              color: statusColors[j.status] || 'var(--text-muted)',
            }}
          >
            {j.status}
          </div>
        </li>
      ))}
    </ul>
  )
}
