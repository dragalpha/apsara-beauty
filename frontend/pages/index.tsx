import { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null)
  }

  const onUpload = async () => {
    if (!file) return
    setLoading(true)
    setResult(null)
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${backendUrl}/analyze`, { method: 'POST', body: form })
    const data = await res.json()
    setResult(data)
    setLoading(false)
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


