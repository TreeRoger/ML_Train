import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { JobDetail, Metrics } from '../types'

const API = '/api/v1'

export function JobDetail({ jobId, onClose }: { jobId: string; onClose: () => void }) {
  const [job, setJob] = useState<JobDetail | null>(null)
  const [metrics, setMetrics] = useState<Metrics | null>(null)

  useEffect(() => {
    fetch(`${API}/jobs/${jobId}`)
      .then((r) => r.json())
      .then(setJob)
      .catch(console.error)
  }, [jobId])

  useEffect(() => {
    const t = setInterval(() => {
      fetch(`${API}/jobs/${jobId}/metrics`)
        .then((r) => r.json())
        .then((d) => setMetrics(d.metrics || null))
        .catch(() => {})
    }, 3000)
    return () => clearInterval(t)
  }, [jobId])

  if (!job) return <p style={{ padding: '2rem' }}>Loading...</p>

  const lossData = metrics?.loss?.map((m) => ({ step: m.step, loss: m.value })) || []
  const accData = metrics?.accuracy?.map((m) => ({ step: m.step, accuracy: m.value })) || []
  const chartData = lossData.length >= accData.length
    ? lossData.map((l, i) => ({ ...l, accuracy: accData[i]?.accuracy ?? null }))
    : accData.map((a, i) => ({ step: a.step, loss: lossData[i]?.loss ?? null, accuracy: a.accuracy }))

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <h2 style={{ margin: 0, fontFamily: 'var(--font-mono)', fontSize: '1rem' }}>{jobId}</h2>
        <button
          onClick={onClose}
          style={{
            padding: '0.5rem 1rem',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            color: 'var(--text)',
            cursor: 'pointer',
          }}
        >
          Close
        </button>
      </div>

      <div style={{ marginBottom: '1.5rem' }}>
        <span
          style={{
            padding: '0.25rem 0.75rem',
            borderRadius: 4,
            background: 'var(--bg-elevated)',
            fontSize: '0.8rem',
            textTransform: 'uppercase',
          }}
        >
          {job.status}
        </span>
        {job.k8s_job_name && (
          <span style={{ marginLeft: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            K8s: {job.k8s_job_name}
          </span>
        )}
      </div>

      {chartData.length > 0 && (
        <div style={{ marginBottom: '2rem', background: 'var(--bg-surface)', padding: '1.5rem', borderRadius: 12, border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '0.9rem' }}>Training Metrics</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="step" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
                labelStyle={{ color: 'var(--text)' }}
              />
              <Legend />
              {lossData.length > 0 && (
                <Line type="monotone" dataKey="loss" stroke="var(--danger)" dot={false} name="Loss" />
              )}
              {accData.length > 0 && (
                <Line type="monotone" dataKey="accuracy" stroke="var(--accent)" dot={false} name="Accuracy" />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {job.config && (
        <div style={{ background: 'var(--bg-surface)', padding: '1.5rem', borderRadius: 12, border: '1px solid var(--border)' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: '0.9rem' }}>Config</h3>
          <pre
            style={{
              margin: 0,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8rem',
              color: 'var(--text-muted)',
              overflow: 'auto',
            }}
          >
            {JSON.stringify(job.config, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
