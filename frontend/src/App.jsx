import { useState, useEffect } from 'react'
import axios from 'axios'
import { Upload, Database, MessageSquare, Send, Loader2, AlertCircle } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function App() {
  const [datasets, setDatasets] = useState([])
  const [selectedDataset, setSelectedDataset] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [asking, setAsking] = useState(false)

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    try {
      const res = await axios.get(`${API_URL}/datasets`)
      setDatasets(res.data)
      if (res.data.length > 0 && !selectedDataset) {
        setSelectedDataset(res.data[0])
      }
    } catch (err) {
      console.error("Failed to fetch datasets", err)
    }
  }

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    setUploading(true)
    setUploadError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const res = await axios.post(`${API_URL}/datasets`, formData)
      pollJobStatus(res.data.job_id, 'ingestion')
    } catch (err) {
      setUploadError(err.response?.data?.detail || err.message)
      setUploading(false)
    }
  }

  const pollJobStatus = async (jobId, type) => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_URL}/jobs/${jobId}`)
        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
          clearInterval(interval)
          if (type === 'ingestion') {
            setUploading(false)
            if (res.data.status === 'COMPLETED') {
               fetchDatasets()
               setSelectedDataset({id: res.data.result.dataset_id, name: "New Dataset"})
            } else {
               setUploadError(res.data.error)
            }
          } else if (type === 'query') {
            setAsking(false)
            setMessages(prev => {
              const updated = [...prev]
              const lastIdx = updated.length - 1
              if (res.data.status === 'COMPLETED') {
                updated[lastIdx] = { role: 'assistant', ...res.data.result }
              } else {
                updated[lastIdx] = { role: 'assistant', answer: `Error: ${res.data.error}`, isError: true }
              }
              return updated
            })
          }
        }
      } catch (err) {
        clearInterval(interval)
        if (type === 'ingestion') {
          setUploading(false)
          setUploadError('Polling failed')
        } else {
          setAsking(false)
        }
      }
    }, 1000)
  }

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!input.trim() || !selectedDataset) return

    const question = input
    setInput('')
    setMessages(prev => [...prev, { role: 'user', answer: question }])
    
    setAsking(true)
    setMessages(prev => [...prev, { role: 'assistant', isLoading: true }])
    
    try {
      const res = await axios.post(`${API_URL}/query`, {
        dataset_id: selectedDataset.id,
        question: question
      })
      pollJobStatus(res.data.job_id, 'query')
    } catch (err) {
      setAsking(false)
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { role: 'assistant', answer: err.message, isError: true }
        return updated
      })
    }
  }

  return (
    <div className="flex h-screen bg-neutral-900 text-neutral-100 font-sans w-full">
      <div className="w-64 bg-neutral-950 border-r border-neutral-800 p-4 flex flex-col">
        <div className="flex items-center gap-2 mb-8 text-xl font-bold text-blue-400">
          <Database className="w-6 h-6" />
          <span>SchemaLens</span>
        </div>

        <div className="mb-6">
          <h2 className="text-xs uppercase tracking-wider text-neutral-500 font-semibold mb-3">Datasets</h2>
          
          <label className="flex items-center justify-center gap-2 w-full p-2 mb-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md cursor-pointer transition-colors text-sm font-medium">
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? 'Processing...' : 'Upload CSV'}
            <input type="file" accept=".csv" className="hidden" onChange={handleUpload} disabled={uploading} />
          </label>
          
          {uploadError && (
            <div className="text-red-400 text-xs flex items-start gap-1 mb-4 bg-red-400/10 p-2 rounded">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          <div className="space-y-1 overflow-y-auto max-h-[50vh]">
            {datasets.map(d => (
              <button
                key={d.id}
                onClick={() => setSelectedDataset(d)}
                className={`w-full text-left p-2 rounded-md text-sm truncate flex items-center gap-2 ${selectedDataset?.id === d.id ? 'bg-neutral-800 text-white' : 'text-neutral-400 hover:bg-neutral-800/50 hover:text-neutral-200'}`}
              >
                <Database className="w-3 h-3" />
                {d.name}
              </button>
            ))}
            {datasets.length === 0 && !uploading && (
              <div className="text-neutral-500 text-sm text-center py-4">No datasets uploaded</div>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-neutral-800 flex items-center px-6">
          {selectedDataset ? (
            <div className="flex items-center gap-2">
              <span className="text-neutral-400">Current context:</span>
              <span className="font-semibold">{selectedDataset.name}</span>
            </div>
          ) : (
            <div className="text-neutral-500">Please select or upload a dataset to begin</div>
          )}
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && selectedDataset && (
            <div className="h-full flex flex-col items-center justify-center text-neutral-500 space-y-4">
              <MessageSquare className="w-12 h-12 opacity-20" />
              <h3 className="text-lg">Ask me anything about {selectedDataset.name}</h3>
              <div className="flex gap-2">
                <span className="bg-neutral-800 px-3 py-1 rounded-full text-xs">Top 10 products by revenue</span>
                <span className="bg-neutral-800 px-3 py-1 rounded-full text-xs">Total sales this month</span>
              </div>
            </div>
          )}
          
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl rounded-2xl px-5 py-4 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-neutral-800 text-neutral-200'}`}>
                {msg.isLoading ? (
                  <div className="flex items-center gap-2 text-neutral-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing data...
                  </div>
                ) : (
                  <>
                    <div className={msg.isError ? "text-red-400 whitespace-pre-wrap" : "whitespace-pre-wrap"}>{msg.answer}</div>
                    {msg.sql && (
                      <div className="mt-4 pt-4 border-t border-neutral-700">
                        <div className="text-xs text-neutral-500 mb-2 uppercase tracking-wide font-semibold">Generated SQL</div>
                        <pre className="bg-neutral-900 p-3 rounded-md text-xs text-blue-300 overflow-x-auto">
                          <code>{msg.sql}</code>
                        </pre>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-neutral-800">
          <form onSubmit={handleAsk} className="max-w-4xl mx-auto relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={selectedDataset ? "Ask a question in plain English..." : "Upload a dataset first"}
              disabled={!selectedDataset || asking}
              className="w-full bg-neutral-900 border border-neutral-700 rounded-full py-4 pl-6 pr-14 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-50 transition-all"
            />
            <button
              type="submit"
              disabled={!input.trim() || !selectedDataset || asking}
              className="absolute right-2 top-2 bottom-2 aspect-square flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white rounded-full disabled:opacity-50 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-center mt-2 text-xs text-neutral-500">
            SchemaLens can make mistakes. Verify important SQL queries.
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
