import { useState } from 'react'
import './App.css'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const examples = [
    "Do bhaiyon ke darmiyan zameen ki warasat ka dispute hai",
    "Sister ko inheritance se exclude karne ki koshish ki gai hai oral gift ke zariye",
    "Mutation mein ghalat entry hai, kaise challenge karein?",
    "Co-sharer ne exclusive possession le liya hai, partition ka suit maintainable hai?",
    "Predeceased son ke children ka hissa kya hoga under MFLO Section 4?"
  ]

  const handleSearch = async (q = query) => {
    if (!q.trim() || q.trim().length < 5) {
      setError('Please enter a meaningful legal query (at least 5 characters)')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, top_k: 8 })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Search failed')
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to connect to backend. Make sure backend is running on port 8000.')
    } finally {
      setLoading(false)
    }
  }

  const handleExample = (ex) => {
    setQuery(ex)
    handleSearch(ex)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">⚖️</span>
            <div>
              <h1>Pakistan Legal AI</h1>
              <p>AI-Powered Legal Research & Case Recommendation System</p>
            </div>
          </div>
          <div className="badge">FYP Demo • Sample Data</div>
        </div>
      </header>

      <main className="main">
        <section className="search-section">
          <h2>Apna Case ya Sawal Likhein</h2>
          <p className="subtitle">Urdu ya English mein likhein — System relevant Constitution Articles, Acts, Judgments aur Legal Arguments suggest karega</p>
          
          <div className="search-box">
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='Example: "Do bhaiyon ke darmiyan zameen ki warasat ka dispute hai..."'
              rows={3}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSearch()
                }
              }}
            />
            <button 
              onClick={() => handleSearch()} 
              disabled={loading}
              className="search-btn"
            >
              {loading ? (
                <>
                  <span className="spinner"></span> Researching...
                </>
              ) : (
                <>🔍 Search Legal Database</>
              )}
            </button>
          </div>

          <div className="examples">
            <span>Try examples:</span>
            {examples.map((ex, i) => (
              <button key={i} className="example-chip" onClick={() => handleExample(ex)}>
                {ex.length > 55 ? ex.slice(0, 55) + '...' : ex}
              </button>
            ))}
          </div>
        </section>

        {error && (
          <div className="error-box">
            ⚠️ {error}
          </div>
        )}

        {result && (
          <div className="results">
            <div className="query-echo">
              <strong>Query:</strong> {result.query}
            </div>

            {result.constitution_articles?.length > 0 && (
              <section className="result-section">
                <h3>📜 Relevant Constitution Articles</h3>
                <div className="cards">
                  {result.constitution_articles.map((art) => (
                    <div key={art.id} className="card constitution">
                      <div className="card-header">
                        <h4>{art.title}</h4>
                        {art.score && <span className="score">{(art.score * 100).toFixed(0)}% match</span>}
                      </div>
                      <p className="card-text">{art.text}</p>
                      <div className="card-footer">{art.source}</div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {result.relevant_acts?.length > 0 && (
              <section className="result-section">
                <h3>📖 Relevant Acts & Sections</h3>
                <div className="cards">
                  {result.relevant_acts.map((act) => (
                    <div key={act.id} className="card act">
                      <div className="card-header">
                        <h4>{act.act_name} — {act.section}</h4>
                        {act.score && <span className="score">{(act.score * 100).toFixed(0)}% match</span>}
                      </div>
                      <p className="card-title">{act.title}</p>
                      <p className="card-text">{act.text}</p>
                      <div className="card-footer">{act.source}</div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {result.similar_judgments?.length > 0 && (
              <section className="result-section">
                <h3>⚖️ Similar Past Judgments (Precedents)</h3>
                <div className="cards">
                  {result.similar_judgments.map((jud) => (
                    <div key={jud.id} className="card judgment">
                      <div className="card-header">
                        <h4>{jud.case_name}</h4>
                        {jud.score && <span className="score">{(jud.score * 100).toFixed(0)}% match</span>}
                      </div>
                      <div className="meta">
                        <span className="citation">{jud.citation}</span>
                        <span>{jud.court} • {jud.year}</span>
                      </div>
                      {jud.judges?.length > 0 && (
                        <p className="judges">Judges: {jud.judges.join(', ')}</p>
                      )}
                      <p className="card-text"><strong>Summary:</strong> {jud.summary}</p>
                      {jud.key_holdings?.length > 0 && (
                        <div className="holdings">
                          <strong>Key Holdings:</strong>
                          <ul>
                            {jud.key_holdings.map((h, i) => <li key={i}>{h}</li>)}
                          </ul>
                        </div>
                      )}
                      <div className="card-footer">
                        Relevant: {jud.relevant_acts?.join(' • ')}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {result.suggested_arguments?.length > 0 && (
              <section className="result-section">
                <h3>💡 Suggested Legal Arguments</h3>
                <div className="cards">
                  {result.suggested_arguments.map((arg, i) => (
                    <div key={i} className="card argument">
                      <h4>{arg.title}</h4>
                      <p className="card-text">{arg.description}</p>
                      <div className="refs">
                        <strong>References:</strong>
                        <div className="ref-tags">
                          {arg.supporting_references.map((r, j) => (
                            <span key={j} className="ref-tag">{r}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <div className="disclaimer">
              ⚠️ {result.disclaimer}
            </div>
          </div>
        )}

        {!result && !loading && !error && (
          <div className="empty-state">
            <div className="empty-icon">⚖️</div>
            <h3>Ready for Legal Research</h3>
            <p>Type your case description or legal question above, or click an example to see how the system works.</p>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Pakistan Legal AI Research System • Final Year Project Demo • Sample Data Only</p>
        <p>Always verify with original sources (PLD, SCMR, CLC etc.) and consult a qualified lawyer.</p>
      </footer>
    </div>
  )
}

export default App
