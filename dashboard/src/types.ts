export interface Job {
  id: string
  name?: string
  status: string
  created_at?: string
}

export interface JobDetail extends Job {
  config?: Record<string, unknown>
  k8s_job_name?: string
  error_message?: string
  finished_at?: string
}

export interface Metrics {
  [name: string]: { step: number; epoch: number; value: number }[]
}
