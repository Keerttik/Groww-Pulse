import { useState, useEffect } from 'react'
import './App.css'

// Using relative path for production (Railway) so it uses the same host
const API_URL = import.meta.env.DEV ? 'http://localhost:8001/api' : '/api'

// Simple SVG Icons
const Icons = {
  Check: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>,
  Chart: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>,
  Infinity: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h13l4-5-4-5z"></path></svg>, // Actually a tag/label icon, close enough to the diamond
  Shield: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>,
  Search: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>,
  Play: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>,
}

function App() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)

  const fetchRuns = async () => {
    try {
      const res = await fetch(`${API_URL}/runs`)
      if (res.ok) {
        const data = await res.json()
        setRuns(data)
      }
    } catch (err) {
      console.error("Failed to fetch runs:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRuns()
    const interval = setInterval(fetchRuns, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleStartPulse = async () => {
    setStarting(true)
    try {
      const now = new Date()
      const start = new Date(now.getFullYear(), 0, 1)
      const days = Math.floor((now - start) / (24 * 60 * 60 * 1000))
      const weekNumber = Math.ceil((now.getDay() + 1 + days) / 7)
      const weekStr = `${now.getFullYear()}-W${weekNumber.toString().padStart(2, '0')}`

      const res = await fetch(`${API_URL}/runs/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ week: weekStr, force: true, email_mode: 'draft' })
      })

      if (res.ok) {
        setTimeout(fetchRuns, 1000)
      }
    } catch (err) {
      console.error("Failed to start pulse:", err)
    } finally {
      setStarting(false)
    }
  }

  // Generate a fake sparkline SVG for aesthetics based on run id
  const Sparkline = ({ seed }) => {
    const points = [10, 25, 20, 45, 30, 60, 50, 80].map((y, i) => `${i * 30},${100 - (y + (seed % 20))}`).join(' ');
    return (
      <svg viewBox="0 0 210 100" className="sparkline" preserveAspectRatio="none">
        <polyline fill="none" stroke="var(--accent-primary)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" points={points} />
      </svg>
    )
  }

  return (
    <>
      <nav className="navbar">
        <div className="nav-brand">
          <Icons.Chart />
          GROWW PULSE
        </div>
        <div className="nav-search">
          <Icons.Search />
          <input type="text" placeholder="Search for historical runs, themes, or ask a question..." disabled />
        </div>
        <div className="nav-user">US</div>
      </nav>

      <div className="container">
        <section className="hero">
          <h1>UNLOCK AUTOMATED APP REVIEW INTELLIGENCE. <span>NOT NOISE.</span></h1>
          <p>Access Verified Play Store Data & AI-Driven Analytics for Groww.</p>
          <button 
            className="btn-primary" 
            onClick={handleStartPulse} 
            disabled={starting}
          >
            {starting ? <div className="spinner" /> : null}
            {starting ? 'TRIGGERING...' : 'RUN PULSE NOW & FETCH INSIGHTS'}
          </button>
        </section>



        <div className="dashboard-layout">
          <div>
            <h2 className="section-heading">DEEP-DIVE RUN COMPARISON TOOL</h2>
            
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <div className="spinner" style={{ margin: '0 auto', borderColor: 'var(--accent-primary)', borderLeftColor: 'transparent', width: '32px', height: '32px' }} />
              </div>
            ) : runs.length === 0 ? (
              <div className="run-card" style={{ textAlign: 'center', padding: '60px 20px', alignItems: 'center' }}>
                <h3 style={{ color: 'var(--text-secondary)' }}>No runs found</h3>
                <p>Trigger your first Groww Pulse run above.</p>
              </div>
            ) : (
              <div className="runs-grid">
                {runs.map((run, idx) => (
                  <div key={run.run_id} className="run-card">
                    <div className="run-card-header">
                      <div className="run-icon">W</div>
                      <div className="run-title">
                        <h4>Groww Pulse {run.iso_week}</h4>
                        <span className={`run-status ${run.status}`}>{run.status}</span>
                      </div>
                    </div>
                    
                    <div className="metric-row">
                      <div className="metric-label">Reviews Fetched:</div>
                      <div className="metric-value">{run.reviews_fetched || 0}</div>
                    </div>
                    <div className="metric-row">
                      <div className="metric-label">Themes Generated:</div>
                      <div className="metric-value">{run.themes_generated || 0}</div>
                    </div>

                    <Sparkline seed={idx * 13} />

                    <a 
                      href={run.doc_id ? `https://docs.google.com/document/d/${run.doc_id}` : '#'} 
                      target="_blank" 
                      rel="noreferrer"
                      className="btn-outline"
                      style={{ pointerEvents: run.doc_id ? 'auto' : 'none', opacity: run.doc_id ? 1 : 0.5 }}
                    >
                      VIEW FULL ANALYTICS &rarr;
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h2 className="section-heading">HIGH PERFORMING THEMES</h2>
            <div className="sidebar-list">
              <div className="sidebar-pill">Login Issues Spike</div>
              <div className="sidebar-pill">App Crash on KYC</div>
              <div className="sidebar-pill">Positive UI Feedback</div>
              <div className="sidebar-pill">Customer Support Delays</div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default App
