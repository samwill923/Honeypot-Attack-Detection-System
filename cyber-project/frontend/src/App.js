// App.js — Vision UI Fixed Ports Chart
import React, { useEffect, useState, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar
} from "recharts";
import "./App.css";

export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(true);
  const poll = useRef(null);

  const BACKEND = "http://localhost:5000";

  useEffect(() => {
    fetchRows();
    poll.current = setInterval(fetchRows, 2000);
    return () => clearInterval(poll.current);
  }, []);

  async function fetchRows() {
    setLoading(true);
    try {
      const res = await fetch(`${BACKEND}/api/log`);
      if (!res.ok) throw new Error("fetch failed " + res.status);
      const j = await res.json();
      setRows(j.rows || []);
    } catch (e) {
      console.error("fetchRows error:", e);
    }
    setLoading(false);
  }

  function topIPs(n = 5) {
    const counts = {};
    for (const r of rows) counts[r.src_ip] = (counts[r.src_ip] || 0) + 1;
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, n)
      .map(([ip, c]) => ({ ip, c }));
  }

  function byPort() {
    const counts = {};
    for (const r of rows) counts[r.dst_port] = (counts[r.dst_port] || 0) + 1;
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([p, c]) => ({ port: p, count: c }));
  }

  function timeseries() {
    const b = {};
    for (const r of rows) {
      const d = new Date(r.timestamp);
      d.setSeconds(0, 0);
      const key = d.toISOString();
      b[key] = (b[key] || 0) + 1;
    }
    return Object.keys(b).sort().map((k) => ({ time: k, attempts: b[k] }));
  }

  async function simulateAttack(dst_port) {
    try {
      await fetch(`${BACKEND}/api/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dst_port })
      });
      fetchRows();
    } catch (e) { console.error(e); }
  }

  async function toggleListening() {
    try {
      await fetch(`${BACKEND}/api/listen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ listen: !listening })
      });
      setListening(!listening);
    } catch (e) { console.error(e); }
  }

  function downloadCSV() {
    window.location.href = `${BACKEND}/api/download`;
  }

  return (
    <div className="app-layout">
      <main className="main-content">
        {/* Top Header */}
        <header className="top-nav">
          <div>
            <div className="breadcrumbs">Vision Honeypot</div>
            <h1 className="page-title">Dashboard Overview</h1>
          </div>
          <div className="header-controls">
            <button className="btn btn-ghost" onClick={() => simulateAttack(22)}>Sim SSH</button>
            <button className="btn btn-ghost" onClick={() => simulateAttack(80)}>Sim HTTP</button>
            <button className="btn btn-ghost" onClick={downloadCSV}>Export CSV</button>
            <button 
              className={listening ? "btn btn-primary" : "btn btn-danger"} 
              onClick={toggleListening}
              style={{ minWidth: 100 }}
            >
              {listening ? "LISTENING" : "PAUSED"}
            </button>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="grid-container">
          
          {/* Main Chart Card */}
          <div className="card">
            <h2 className="card-title">Traffic Overview</h2>
            <div className="card-subtitle">
              <strong>(+{rows.length})</strong> detected attempts today
            </div>
            <div className="chart-box">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timeseries()}>
                  <defs>
                    <linearGradient id="colorAttempts" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0075ff" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#0075ff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                  <XAxis 
                    dataKey="time" 
                    tickFormatter={(t) => new Date(t).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})} 
                    tick={{ fill: "#fff", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis 
                    tick={{ fill: "#fff", fontSize: 10 }} 
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#0f121d", borderColor: "#fff", borderRadius: "10px" }}
                    itemStyle={{ color: "#fff" }}
                    labelStyle={{ color: "#a0aec0" }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="attempts" 
                    stroke="#0075ff" 
                    strokeWidth={4} 
                    dot={false}
                    activeDot={{ r: 8, fill:"#00c6ff" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Side Stats Card */}
          <div className="card">
            <h2 className="card-title">Top Attackers</h2>
            <div className="card-subtitle">Most active source IPs</div>
            
            <div style={{ display:'flex', flexDirection:'column', gap:4, marginBottom: 20 }}>
              {topIPs(5).map((x) => (
                <div className="stat-row" key={x.ip}>
                  <div className="ip-badge">{x.ip}</div>
                  <div className="count-badge">{x.c} hits</div>
                </div>
              ))}
              {topIPs(5).length === 0 && <div className="text-muted">No data yet</div>}
            </div>

            <h2 className="card-title">Target Ports</h2>
             {/* FIXED CHART SECTION */}
             <div style={{ height: 160, marginTop: 10 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart layout="vertical" data={byPort()} margin={{ left: 0, right: 20, bottom: 0, top: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis 
                      dataKey="port" 
                      type="category" 
                      width={50} 
                      tick={{ fill: "#fff", fontSize: 12, fontWeight: 700 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip 
                      cursor={{fill: 'rgba(255,255,255,0.05)'}} 
                      contentStyle={{ backgroundColor: "#0f121d", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
                    />
                    <Bar dataKey="count" fill="#0075ff" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
             </div>
          </div>

          {/* Full Width Table Card */}
          <div className="card full-width">
            <h2 className="card-title">Connection Logs</h2>
            <div className="card-subtitle">Real-time incoming traffic</div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Source IP</th>
                    <th>Src Port</th>
                    <th>Dst Port</th>
                    <th>Payload Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.slice().reverse().map((r, i) => (
                    <tr key={i}>
                      <td>{new Date(r.timestamp).toLocaleString()}</td>
                      <td style={{ fontWeight: "bold" }}>{r.src_ip}</td>
                      <td>{r.src_port}</td>
                      <td>
                        <span style={{ 
                          background: r.dst_port === 22 ? "var(--danger)" : "var(--primary)",
                          padding: "2px 6px", borderRadius: 4, fontSize: 10
                        }}>
                          {r.dst_port}
                        </span>
                      </td>
                      <td className="preview-text">{r.recv_preview || "EMPTY"}</td>
                    </tr>
                  ))}
                  {rows.length === 0 && <tr><td colSpan="5" style={{textAlign:"center", color:"gray"}}>Waiting for traffic...</td></tr>}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}