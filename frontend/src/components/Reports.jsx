import { useEffect, useMemo, useState, useRef } from 'react';
import api from '../api';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend } from 'recharts';
import { toast } from 'react-toastify';

const PIE_COLORS = ['#00d68f','#0066ff','#ffa502','#ff4757','#7bed9f','#70a1ff'];
const STALE_MS   = 60_000;

function ChartCard({ title, children }) {
  return (
    <div className="col-md-6 mb-4">
      <div className="card" style={{ height:'100%' }}>
        <div className="card-header">{title}</div>
        <div className="card-body">{children}</div>
      </div>
    </div>
  );
}

export default function Reports() {
  const today = new Date().toISOString().slice(0, 10);
  const thirtyDaysAgo = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);

  const [fromDate, setFromDate] = useState(thirtyDaysAgo);
  const [toDate,   setToDate]   = useState(today);
  const [daily,    setDaily]    = useState([]);
  const [payments, setPayments] = useState([]);
  const [top,      setTop]      = useState([]);
  const [monthly,  setMonthly]  = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [profit,   setProfit]   = useState([]);
  const [eod,      setEod]      = useState(null);
  const [eodDate,  setEodDate]  = useState(today);
  const [loading,  setLoading]  = useState(false);
  const cacheRef   = useRef({ data: null, ts: 0, key: '' });

  const cacheKey = `${fromDate}|${toDate}`;

  const load = async (force = false) => {
    const now = Date.now();
    if (!force && cacheRef.current.key === cacheKey && now - cacheRef.current.ts < STALE_MS) {
      const d = cacheRef.current.data;
      setDaily(d.daily); setPayments(d.payments); setTop(d.top);
      setMonthly(d.monthly); setExpenses(d.expenses); setProfit(d.profit);
      return;
    }
    setLoading(true);
    const params = { params: { from_date: fromDate, to_date: toDate } };
    try {
      const [a, b, c, d, e, f] = await Promise.all([
        api.get('/reports/daily-sales/',    params),
        api.get('/reports/payment-methods/', params),
        api.get('/reports/top-services/',   params),
        api.get('/reports/monthly-sales/',  params),
        api.get('/reports/daily-expenses/', params),
        api.get('/reports/profit-summary/', params),
      ]);
      const arr = (x) => Array.isArray(x) ? x : [];
      const data = { daily: arr(a.data), payments: arr(b.data), top: arr(c.data), monthly: arr(d.data), expenses: arr(e.data), profit: arr(f.data) };
      cacheRef.current = { data, ts: Date.now(), key: cacheKey };
      setDaily(data.daily); setPayments(data.payments); setTop(data.top);
      setMonthly(data.monthly); setExpenses(data.expenses); setProfit(data.profit);
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.error || 'Failed to load reports.');
      console.error(err.response?.data || err);
    }
    finally { setLoading(false); }
  };

  const loadEod = async () => {
    try {
      const r = await api.get('/reports/eod-summary/', { params: { date: eodDate } });
      setEod(r.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || err.response?.data?.error || 'Failed to load end-of-day summary.');
      console.error(err.response?.data || err);
    }
  };

  useEffect(() => { load(); }, [fromDate, toDate]);

  const totalRevenue      = useMemo(() => daily.reduce((s, i) => s + Number(i.total_sales || 0), 0), [daily]);
  const totalExpensesSum  = useMemo(() => expenses.reduce((s, i) => s + Number(i.total_expenses || 0), 0), [expenses]);
  const totalTransactions = useMemo(() => daily.reduce((s, i) => s + Number(i.transactions || 0), 0), [daily]);

  const printEod = () => {
    const w = window.open('', '_blank');
    if (!w || !eod) return;
    w.document.write(`<html><head><title>End of Day Report</title><style>body{font-family:sans-serif;padding:24px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #eee}h2,h3{margin:16px 0 8px}</style></head><body>
      <h2>Qubits Cyber Services — End of Day Report</h2>
      <p><strong>Date:</strong> ${eod.date}</p>
      <table><tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Total Revenue</td><td>KES ${eod.total_revenue.toLocaleString()}</td></tr>
        <tr><td>Cash Collected</td><td>KES ${eod.cash_collected.toLocaleString()}</td></tr>
        <tr><td>M-PESA Collected</td><td>KES ${eod.mpesa_collected.toLocaleString()}</td></tr>
        <tr><td>Total Expenses</td><td>KES ${eod.total_expenses.toLocaleString()}</td></tr>
        <tr><td>Net Profit</td><td>KES ${eod.net_profit.toLocaleString()}</td></tr>
        <tr><td>Transactions</td><td>${eod.total_transactions}</td></tr>
      </table>
      <h3>Top Services</h3>
      <table><tr><th>Service</th><th>Qty</th><th>Revenue</th></tr>
        ${eod.top_services.map(s => `<tr><td>${s.service}</td><td>${s.quantity}</td><td>KES ${s.revenue.toLocaleString()}</td></tr>`).join('')}
      </table>
      <p style="margin-top:24px;color:#888">Printed ${new Date().toLocaleString('en-KE')}</p>
    </body></html>`);
    w.print();
  };

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-3" style={{ flexWrap:'wrap', gap:12 }}>
        <div>
          <h2 className="fw-bold">Reports Dashboard</h2>
          <p className="text-muted">Revenue, expenses, and business performance.</p>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
          <label className="form-label" style={{ marginBottom:0 }}>From</label>
          <input type="date" className="form-control form-control-sm" value={fromDate} style={{ width:140 }} onChange={e => setFromDate(e.target.value)} />
          <label className="form-label" style={{ marginBottom:0 }}>To</label>
          <input type="date" className="form-control form-control-sm" value={toDate}   style={{ width:140 }} onChange={e => setToDate(e.target.value)} />
          <button className="btn btn-outline-secondary btn-sm" onClick={() => load(true)} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="row mb-4">
        {[
          { label:'Revenue',     value:`KES ${totalRevenue.toLocaleString()}`,            accent:'#00d68f' },
          { label:'Expenses',    value:`KES ${totalExpensesSum.toLocaleString()}`,         accent:'#ff4757' },
          { label:'Net Profit',  value:`KES ${(totalRevenue - totalExpensesSum).toLocaleString()}`, accent:'#0066ff' },
          { label:'Transactions', value:totalTransactions,                                 accent:'#ffa502' },
        ].map((s, i) => (
          <div className="col-md-3" key={i}>
            <div className="stat-card" style={{ borderLeft:`3px solid ${s.accent}` }}>
              <h6>{s.label}</h6>
              <h3 style={{ color:s.accent }}>{s.value}</h3>
              <small>{fromDate} → {toDate}</small>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="row">
        <ChartCard title="Daily Sales Revenue">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={daily}><CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize:11 }} /><YAxis tick={{ fontSize:11 }} />
              <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} />
              <Line dataKey="total_sales" name="Revenue" stroke="#00d68f" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Payment Methods">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={payments} dataKey="total" nameKey="method" outerRadius={90}
                label={({ method, percent }) => `${method} ${(percent*100).toFixed(0)}%`}>
                {payments.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top-Selling Services">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={top}><CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="service" tick={{ fontSize:10 }} /><YAxis tick={{ fontSize:11 }} />
              <Tooltip />
              <Bar dataKey="quantity_sold" name="Qty Sold" fill="#0066ff" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Monthly Revenue">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={monthly}><CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" tick={{ fontSize:11 }} /><YAxis tick={{ fontSize:11 }} />
              <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} />
              <Line dataKey="total_sales" name="Revenue" stroke="#7bed9f" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Daily Expenses">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={expenses}><CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize:11 }} /><YAxis tick={{ fontSize:11 }} />
              <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} />
              <Bar dataKey="total_expenses" name="Expenses" fill="#ff4757" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Revenue vs Expenses vs Profit">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={profit}><CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize:11 }} /><YAxis tick={{ fontSize:11 }} />
              <Tooltip formatter={v => `KES ${Number(v).toLocaleString()}`} />
              <Bar dataKey="revenue"  name="Revenue"  fill="#00d68f" radius={[4,4,0,0]} />
              <Bar dataKey="expenses" name="Expenses" fill="#ff4757" radius={[4,4,0,0]} />
              <Bar dataKey="profit"   name="Profit"   fill="#0066ff" radius={[4,4,0,0]} />
              <Legend />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* End-of-Day Summary */}
      <div className="card mt-4">
        <div className="card-header">
          <span>End-of-Day Summary</span>
          <div style={{ display:'flex', gap:8, alignItems:'center' }}>
            <input type="date" className="form-control form-control-sm" value={eodDate} style={{ width:140 }} onChange={e => setEodDate(e.target.value)} />
            <button className="btn btn-sm btn-primary" onClick={loadEod}>Load</button>
            {eod && <button className="btn btn-sm btn-dark" onClick={printEod}>🖨 Print</button>}
          </div>
        </div>
        {eod ? (
          <div className="card-body">
            <div className="row mb-3">
              {[
                { label:'Revenue',       value:`KES ${eod.total_revenue.toLocaleString()}`,     color:'#00d68f' },
                { label:'Cash',          value:`KES ${eod.cash_collected.toLocaleString()}`,     color:'#7bed9f' },
                { label:'M-PESA',        value:`KES ${eod.mpesa_collected.toLocaleString()}`,    color:'#0066ff' },
                { label:'Expenses',      value:`KES ${eod.total_expenses.toLocaleString()}`,     color:'#ff4757' },
                { label:'Net Profit',    value:`KES ${eod.net_profit.toLocaleString()}`,         color:'#ffa502' },
                { label:'Transactions',  value:eod.total_transactions,                           color:'var(--text-muted)' },
              ].map((s, i) => (
                <div className="col-md-2" key={i} style={{ padding:'6px 10px' }}>
                  <div style={{ fontSize:11, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:4 }}>{s.label}</div>
                  <div style={{ fontSize:18, fontFamily:'var(--mono)', fontWeight:700, color:s.color }}>{s.value}</div>
                </div>
              ))}
            </div>
            <table className="table">
              <thead><tr><th>Top Service</th><th>Qty</th><th>Revenue</th></tr></thead>
              <tbody>
                {eod.top_services.map((s, i) => (
                  <tr key={i}>
                    <td>{s.service}</td>
                    <td>{s.quantity}</td>
                    <td style={{ fontFamily:'var(--mono)', color:'var(--accent)' }}>KES {Number(s.revenue).toLocaleString()}</td>
                  </tr>
                ))}
                {!eod.top_services.length && <tr><td colSpan={3} style={{ color:'var(--text-muted)', textAlign:'center' }}>No sales on this date.</td></tr>}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card-body" style={{ textAlign:'center', color:'var(--text-muted)', padding:'24px 0' }}>
            Select a date and click Load to see the end-of-day summary.
          </div>
        )}
      </div>
    </div>
  );
}
