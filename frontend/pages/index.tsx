import { useMemo, useState } from 'react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [chatInput, setChatInput] = useState('')
  const [chatAnswer, setChatAnswer] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [chatSuggestions, setChatSuggestions] = useState<string[]>([])
  const backendUrl = useMemo(() => {
    const url = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'http://localhost:8000'
    return url.replace(/\/$/, '')
  }, [])

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null)
  }

  const onAsk = async () => {
    if (!chatInput.trim()) return
    setChatAnswer(null)
    setError(null)
    try {
      const res = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: chatInput.trim(), session_id: sessionId || undefined })
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`HTTP ${res.status}: ${text}`)
      }
      const data = await res.json()
      setChatAnswer(data?.response || 'No answer')
      if (data?.session_id) setSessionId(data.session_id)
      setChatSuggestions(Array.isArray(data?.suggestions) ? data.suggestions : [])
    } catch (e: any) {
      setError(e?.message || 'Chat failed')
    }
  }

  const onUsePhotoInChat = async () => {
    if (!file) { setError('Upload a photo first'); return }
    try {
      // Ensure session
      let sid = sessionId
      if (!sid) {
        const init = await fetch(`${backendUrl}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: 'Hi' }) })
        const d = await init.json()
        sid = d?.session_id
        if (sid) setSessionId(sid)
      }
      if (!sid) throw new Error('Failed to init chat session')
      const form = new FormData()
      form.append('session_id', sid)
      form.append('file', file)
      const res = await fetch(`${backendUrl}/chat/analyze-image`, { method: 'POST', body: form })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`HTTP ${res.status}: ${text}`)
      }
      const data = await res.json()
      setChatAnswer(data?.response || 'Image analyzed')
    } catch (e: any) {
      setError(e?.message || 'Failed to analyze in chat')
    }
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
      <h1 className="text-4xl font-bold mb-6 text-indigo-800">Apsara - AI Skincare</h1>
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-xl border border-indigo-100">
        <h2 className="text-xl font-semibold mb-4 text-indigo-700">Upload Your Skin Photo</h2>
        <div className="mb-4 p-4 border-2 border-dashed border-gray-300 rounded-lg text-center hover:border-indigo-300 transition-colors">
          <input 
            type="file" 
            accept="image/*" 
            onChange={onFileChange} 
            className="hidden" 
            id="fileInput" 
          />
          <label htmlFor="fileInput" className="cursor-pointer block">
            {file ? (
              <div className="text-indigo-600">
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-gray-500">Click to change</p>
              </div>
            ) : (
              <div>
                <p className="text-gray-500">Click to select an image</p>
                <p className="text-sm text-gray-400">or drag and drop</p>
              </div>
            )}
          </label>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={onUpload} 
            disabled={!file || loading} 
            className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-md disabled:opacity-50 hover:bg-indigo-700 transition-colors font-medium"
          >
            {loading ? 'Analyzing...' : 'Analyze Skin'}
          </button>
          <button 
            onClick={onUsePhotoInChat} 
            disabled={!file} 
            className="flex-1 px-4 py-3 bg-green-600 text-white rounded-md disabled:opacity-50 hover:bg-green-700 transition-colors font-medium"
          >
            Use Photo in Chat
          </button>
        </div>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <div>Backend: <code className="bg-gray-100 px-1 py-0.5 rounded">{backendUrl}</code></div>
        {error && (
          <div className="mt-2 text-red-600">Error: {error}</div>
        )}
      </div>

      {/* Chatbot - always visible */}
      <section className="mt-8 grid gap-6">
        <div className="bg-white p-6 rounded-lg shadow-lg border border-indigo-100">
          <h2 className="text-xl font-semibold mb-4 text-indigo-700">Skincare Chatbot</h2>
          <div className="flex gap-2">
            <input 
              value={chatInput} 
              onChange={(e) => setChatInput(e.target.value)} 
              onKeyPress={(e) => e.key === 'Enter' && onAsk()}
              placeholder="Ask a skincare question..." 
              className="flex-1 border border-gray-300 rounded-md px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500" 
            />
            <button 
              onClick={onAsk} 
              className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
            >
              Ask
            </button>
          </div>
          
          {chatAnswer && (
            <div className="mt-4 p-4 bg-indigo-50 rounded-lg whitespace-pre-wrap text-gray-800 border-l-4 border-indigo-400">
              {chatAnswer}
            </div>
          )}
          
          {chatSuggestions?.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Suggested questions:</p>
              <div className="flex flex-wrap gap-2">
                {chatSuggestions.map((s) => (
                  <button 
                    key={s} 
                    onClick={() => { setChatInput(s); onAsk() }} 
                    className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-md text-sm transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {result && (
          <>
          <div className="bg-white p-6 rounded-lg shadow-lg border border-indigo-100">
            <div className="flex flex-col md:flex-row gap-6">
              {result.image_path && (
                <div className="md:w-1/3">
                  <img 
                    src={`${backendUrl}/${result.image_path}`} 
                    alt="Analyzed skin" 
                    className="w-full rounded-lg shadow-md" 
                  />
                </div>
              )}
              <div className="md:w-2/3">
                <h2 className="text-xl font-semibold mb-4 text-indigo-700">Analysis Results</h2>
                <div className="space-y-3">
                  <div className="p-3 bg-indigo-50 rounded-md">
                    <span className="text-gray-600">Skin Type:</span> 
                    <span className="ml-2 font-semibold text-indigo-800">{result.skin_type}</span>
                  </div>
                  
                  <div className="p-3 bg-indigo-50 rounded-md">
                    <span className="text-gray-600">Concerns:</span>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {result.concerns?.map((concern: string, i: number) => (
                        <span key={i} className="px-2 py-1 bg-white rounded-full text-sm font-medium text-indigo-700 shadow-sm">
                          {concern}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="p-3 bg-indigo-50 rounded-md">
                    <span className="text-gray-600">Recommendations:</span>
                    <p className="mt-1 text-indigo-800">{result.recommendations}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-lg border border-indigo-100">
            <h2 className="text-xl font-semibold mb-4 text-indigo-700">Recommended Products</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {result.products?.map((p: any) => (
                <div key={p.id} className="border border-gray-200 p-4 rounded-lg hover:shadow-md transition-shadow">
                  <div className="font-medium text-lg text-indigo-700">{p.name}</div>
                  <div className="text-sm text-gray-600 mb-2">{p.brand} · {p.category}</div>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {p.concerns?.map((c: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-gray-600">
                        {c}
                      </span>
                    ))}
                  </div>
                  {p.url && (
                    <a 
                      className="inline-block px-3 py-1 bg-indigo-100 text-indigo-700 rounded-md text-sm hover:bg-indigo-200 transition-colors" 
                      href={p.url} 
                      target="_blank" 
                      rel="noreferrer"
                    >
                      View Product
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
          </>
        )}
      </section>
    </main>
  )
}


