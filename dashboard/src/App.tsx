import { useState, useEffect } from 'react'
import { JobList } from './components/JobList'
import { JobDetail } from './components/JobDetail'
import type { Job } from './types'

const API = '/api/v1'

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API}/jobs`)
      .then((r) => r.json())
      .then((d) => setJobs(d.jobs || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <header
        style={{
          padding: '1rem 2rem',
          borderBottom: '1px solid var(--border)',
          background: 'var(--bg-surface)',
        }}
      >
        <h1
          style={{
            margin: 0,
            fontFamily: 'var(--font-mono)',
            fontSize: '1.25rem',
            fontWeight: 600,
            color: 'var(--accent)',
          }}
        >
          ml-train
        </h1>
        <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Distributed ML Training Orchestrator
        </p>
      </header>

      <main style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <aside
          style={{
            width: 320,
            borderRight: '1px solid var(--border)',
            background: 'var(--bg-surface)',
            overflow: 'auto',
          }}
        >
          {loading ? (
            <p style={{ padding: '2rem', color: 'var(--text-muted)' }}>Loading jobs...</p>
          ) : (
            <JobList jobs={jobs} selected={selected} onSelect={setSelected} />
          )}
        </aside>

        <section style={{ flex: 1, overflow: 'auto', background: 'var(--bg-deep)' }}>
          {selected ? (
            <JobDetail jobId={selected} onClose={() => setSelected(null)} />
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: 'var(--text-muted)',
              }}
            >
              Select a job or submit a new one via API
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
