import { useMemo, useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const backendUrl = useMemo(() => {
    const url = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000'
    return url.replace(/\/$/, '')
  }, [])

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null)
  }

  const onUpload = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    setError(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch(`${backendUrl}/analyze`, { method: 'POST', body: form })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`HTTP ${res.status}: ${text}`)
      }
      const ct = res.headers.get('content-type') || ''
      const data = ct.includes('application/json') ? await res.json() : await res.text()
      if (typeof data !== 'object') {
        throw new Error('Unexpected response from server')
      }
      setResult(data)
    } catch (e: any) {
      setError(e?.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-6">Apsara - AI Skincare</h1>
      <div className="bg-white p-6 rounded shadow max-w-xl">
        <input type="file" accept="image/*" onChange={onFileChange} className="mb-4" />
        <button onClick={onUpload} disabled={!file || loading} className="px-4 py-2 bg-indigo-600 text-white rounded disabled:opacity-50">
          {loading ? 'Analyzing…' : 'Analyze Skin'}
        </button>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <div>Backend: <code className="bg-gray-100 px-1 py-0.5 rounded">{backendUrl}</code></div>
        {error && (
          <div className="mt-2 text-red-600">Error: {error}</div>
        )}
      </div>

      {result && (
        <section className="mt-8 grid gap-6">
          <div className="bg-white p-6 rounded shadow">
            <h2 className="text-xl font-semibold mb-2">Results</h2>
            <p>Skin type: <b>{result.skin_type}</b></p>
            <p>Concerns: {result.concerns?.join(', ')}</p>
            <p>Advice: {result.recommendations}</p>
            {result.image_path && (
              <img src={`${backendUrl}/${result.image_path}`} alt="upload" className="mt-3 w-64 rounded" />
            )}
          </div>

          <div className="bg-white p-6 rounded shadow">
            <h2 className="text-xl font-semibold mb-2">Recommended Products</h2>
            <ul className="space-y-3">
              {result.products?.map((p: any) => (
                <li key={p.id} className="border p-3 rounded">
                  <div className="font-medium">{p.name}</div>
                  <div className="text-sm text-gray-600">{p.brand} · {p.category}</div>
                  {p.url && (<a className="text-indigo-600 text-sm" href={p.url} target="_blank" rel="noreferrer">View</a>)}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-white p-6 rounded shadow">
            <h2 className="text-xl font-semibold mb-2">YouTube Reviews</h2>
            <ul className="grid md:grid-cols-2 gap-4">
              {result.videos?.map((v: any) => (
                <li key={v.url} className="border rounded overflow-hidden">
                  {v.thumbnail && <img src={v.thumbnail} alt={v.title} className="w-full" />}
                  <div className="p-3">
                    <a href={v.url} target="_blank" rel="noreferrer" className="font-medium text-indigo-700">{v.title}</a>
                    <div className="text-sm text-gray-600">{v.channel}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </main>
  )
}


