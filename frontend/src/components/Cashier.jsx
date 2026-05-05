import { useEffect, useRef, useState, useCallback } from 'react';
import api from '../api';
import logo from '../assets/logo.svg';
import { toast } from 'react-toastify';

const CATEGORY_ORDER = ['PRINTING','SCANNING','GOVERNMENT','INTERNET','FINANCIAL','DOCUMENTS','PHONE','OTHER'];
const CATEGORY_LABELS = { PRINTING:'Printing', SCANNING:'Scanning', GOVERNMENT:'Government Services', INTERNET:'Internet & Email', FINANCIAL:'Financial Services', DOCUMENTS:'Documents', PHONE:'Phone Services', OTHER:'Other' };

export default function Cashier({ user }) {
  const today = new Date().toISOString().slice(0, 16); // YYYY-MM-DDTHH:MM
  const [products, setProducts]       = useState([]);
  const [cart, setCart]               = useState([]);
  const [phone, setPhone]             = useState('');
  const [cashPaid, setCashPaid]       = useState('');
  const [receipt, setReceipt]         = useState(null);
  const [pendingMpesa, setPendingMpesa] = useState(null);
  const [loadingCash, setLoadingCash] = useState(false);
  const [loadingMpesa, setLoadingMpesa] = useState(false);
  const [search, setSearch]           = useState('');
  const [openCats, setOpenCats]       = useState({});
  const [saleDate, setSaleDate]       = useState(today);  // Staff can backdate sales
  const pollingRef  = useRef(null);
  const searchRef   = useRef(null);

  useEffect(() => {
    api.get('/products/').then(r => {
      setProducts(r.data);
      // open all categories by default
      const cats = {};
      r.data.forEach(p => { cats[p.category || 'OTHER'] = true; });
      setOpenCats(cats);
    }).catch(() => toast.warning('Failed to load services. Is the backend running?'));
    return () => stopPolling();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = e => {
      if (e.key === 'Escape') clearCart();
      if (e.key === 'F1') { e.preventDefault(); searchRef.current?.focus(); }
      if (e.key === 'Enter' && e.ctrlKey && cashPaid) payCash();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [cashPaid, cart]);

  const stopPolling = () => { if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; } };

  const addToCart = p => {
    setCart(cur => cur.find(i => i.id === p.id)
      ? cur.map(i => i.id === p.id ? { ...i, quantity: i.quantity + 1 } : i)
      : [...cur, { ...p, quantity: 1 }]
    );
    toast.success(`${p.name} added`, { autoClose: 1000 });
  };

  const updateQty   = (id, qty) => setCart(cur => cur.map(i => i.id === id ? { ...i, quantity: Math.max(1, Number(qty)) } : i));
  const removeItem  = id => setCart(cur => cur.filter(i => i.id !== id));
  const clearCart   = () => { setCart([]); setPhone(''); setCashPaid(''); setReceipt(null); };

  const total  = cart.reduce((s, i) => s + Number(i.price) * i.quantity, 0);
  const change = cashPaid ? Math.max(0, Number(cashPaid) - total) : 0;

  const createSale = async () => {
    const payload = {
      items: cart.map(i => ({ product_id: i.id, quantity: i.quantity })),
      customer_phone: phone || undefined,
    };
    // Staff can backdate sales
    if (user?.is_staff && saleDate) {
      payload.sale_date = new Date(saleDate).toISOString();
    }
    const r = await api.post('/sales/', payload);
    return r.data;
  };

  const buildReceipt = (sale, items, method, extra = {}) =>
    setReceipt({ sale, items, method, total: items.reduce((s, i) => s + Number(i.price) * i.quantity, 0), date: new Date().toLocaleString('en-KE'), ...extra });

  const payCash = async () => {
    if (!cart.length) return toast.warning('Add at least one service.');
    if (!cashPaid)    return toast.warning('Enter cash amount received.');
    if (Number(cashPaid) < total) return toast.warning('Cash received is less than total.');
    setLoadingCash(true);
    try {
      const sale  = await createSale();
      const saved = [...cart];
      const r     = await api.post('/payments/cash/', { sale_id: sale.id, amount_paid: cashPaid });
      buildReceipt(sale, saved, 'CASH', { amountPaid: cashPaid, changeDue: r.data.change_due });
      toast.success(`Cash payment OK — Change: KES ${Number(r.data.change_due).toLocaleString()}`);
      setCart([]); setPhone(''); setCashPaid('');
    } catch (err) {
      const detail = err.response?.data?.error || err.response?.data?.detail || 'Cash payment failed. Check backend terminal.';
      toast.error(detail);
      console.error(err.response?.data || err);
    } finally { setLoadingCash(false); }
  };

  const payMpesa = async () => {
    if (!cart.length) return toast.warning('Add at least one service.');
    if (!phone)       return toast.warning('Enter customer M-PESA phone number.');
    setLoadingMpesa(true);
    try {
      const sale  = await createSale();
      const saved = [...cart];
      const r     = await api.post('/payments/stk-push/', { sale_id: sale.id, phone });
      const checkoutRequestId = r.data.checkout_request_id;
      if (!checkoutRequestId) { toast.warning('STK Push sent but no CheckoutRequestID returned.'); return; }
      setPendingMpesa({ checkoutRequestId, saleId: sale.id, status: 'PENDING' });
      toast.info('STK Push sent — ask customer to enter M-PESA PIN…');
      stopPolling();
      let attempts = 0, delay = 2000;
      const poll = async () => {
        attempts++;
        try {
          const s = await api.get(`/payments/status/${checkoutRequestId}/`);
          setPendingMpesa(p => ({ ...p, status: s.data.status, receipt: s.data.mpesa_receipt_number }));
          if (s.data.status === 'PAID') {
            stopPolling();
            toast.success(`M-PESA received — ${s.data.mpesa_receipt_number || 'Recorded'}`);
            buildReceipt(sale, saved, 'M-PESA', { phone, mpesaReceipt: s.data.mpesa_receipt_number });
            setPendingMpesa(null); setCart([]); setPhone(''); setCashPaid(''); return;
          }
          if (['FAILED','CANCELLED'].includes(s.data.status)) {
            stopPolling(); setPendingMpesa(null);
            toast.error(`M-PESA failed: ${s.data.result_description || 'Transaction not completed.'}`); return;
          }
        } catch (e) { console.error(e); }
        if (attempts >= 20) { stopPolling(); toast.warning('Payment still pending — check M-PESA admin.'); return; }
        delay = Math.min(delay * 1.4, 8000);  // exponential backoff
        pollingRef.current = setTimeout(poll, delay);
      };
      pollingRef.current = setTimeout(poll, delay);
    } catch (err) {
      const detail = err.response?.data?.error || err.response?.data?.details || 'M-PESA request failed. Check credentials and backend terminal.';
      toast.error(detail);
      console.error(err.response?.data || err);
    } finally { setLoadingMpesa(false); }
  };

  // Group products by category
  const grouped = {};
  const q = search.toLowerCase();
  products.filter(p => !search || p.name.toLowerCase().includes(q)).forEach(p => {
    const cat = p.category || 'OTHER';
    (grouped[cat] = grouped[cat] || []).push(p);
  });
  const orderedCats = CATEGORY_ORDER.filter(c => grouped[c]);

  const toggleCat = cat => setOpenCats(prev => ({ ...prev, [cat]: !prev[cat] }));

  return (
    <div>
      {pendingMpesa && (
        <div className="alert alert-warning" style={{ display:'flex', alignItems:'center', gap:12, marginBottom:16 }}>
          <div className="mpesa-spinner" />
          <span>M-PESA pending — Sale #{pendingMpesa.saleId} · {pendingMpesa.status}
            {pendingMpesa.receipt && ` · ${pendingMpesa.receipt}`}
          </span>
        </div>
      )}

      <div className="row">
        {/* Services Panel */}
        <div className="col-md-7">
          <div className="card" style={{ minHeight: 400 }}>
            <div className="card-header">
              <span>Services</span>
              <input ref={searchRef} className="form-control form-control-sm" style={{ width:200 }}
                placeholder="Search… (F1)" value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <div className="card-body" style={{ padding:'12px 16px' }}>
              {orderedCats.length === 0 && (
                <p className="text-muted" style={{ textAlign:'center', padding:'32px 0' }}>
                  {products.length === 0 ? 'No services found. Run python manage.py seed_services' : 'No matching services.'}
                </p>
              )}
              {orderedCats.map(cat => (
                <div key={cat} className="cat-section">
                  <button className="cat-header" onClick={() => toggleCat(cat)}>
                    <span className="cat-label">{CATEGORY_LABELS[cat] || cat}</span>
                    <span className="cat-count">{grouped[cat].length}</span>
                    <span className="cat-chevron">{openCats[cat] ? '▾' : '▸'}</span>
                  </button>
                  {openCats[cat] && (
                    <div className="service-grid">
                      {grouped[cat].map(p => (
                        <button key={p.id} className="service-card" onClick={() => addToCart(p)}>
                          <div className="service-name">{p.name}</div>
                          <div className="service-price">KES {Number(p.price).toLocaleString()}</div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Cart Panel */}
        <div className="col-md-5">
          <div className="card cart-panel">
            <div className="card-header">
              Cart
              {cart.length > 0 && <span style={{ color:'var(--accent)', marginLeft:6 }}>({cart.length} items)</span>}
            </div>
            <div className="card-body">
              {!cart.length ? (
                <p className="text-muted" style={{ textAlign:'center', padding:'20px 0' }}>Cart is empty</p>
              ) : (
                <table className="table table-sm">
                  <thead><tr><th>Service</th><th>Unit</th><th>Qty</th><th>Total</th><th></th></tr></thead>
                  <tbody>
                    {cart.map(item => (
                      <tr key={item.id}>
                        <td style={{ fontSize:13 }}>{item.name}</td>
                        <td style={{ fontSize:12, color:'var(--text-muted)' }}>KES {Number(item.price).toLocaleString()}</td>
                        <td style={{ width:64 }}>
                          <input type="number" min="1" className="form-control form-control-sm" value={item.quantity}
                            onChange={e => updateQty(item.id, e.target.value)} />
                        </td>
                        <td style={{ fontFamily:'var(--mono)', fontSize:13 }}>
                          KES {(Number(item.price) * item.quantity).toLocaleString()}
                        </td>
                        <td>
                          <button className="btn btn-sm btn-outline-danger" onClick={() => removeItem(item.id)}>✕</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <div className="total-row">
                <span>Total</span>
                <span style={{ fontFamily:'var(--mono)', color:'var(--accent)', fontSize:22, fontWeight:700 }}>
                  KES {total.toLocaleString()}
                </span>
              </div>

              <hr />

              {user?.is_staff && (
                <>
                  <label className="form-label">Sale Date & Time (optional - staff only)</label>
                  <input type="datetime-local" className="form-control mb-3" value={saleDate} 
                    onChange={e => setSaleDate(e.target.value)} 
                    max={today}
                    title="Leave as current time or backdate for past sales" />
                </>
              )}

              <label className="form-label">Customer M-PESA Phone</label>
              <input className="form-control mb-2" placeholder="2547XXXXXXXX" value={phone} onChange={e => setPhone(e.target.value)} />
              <button className="btn btn-success btn-lg w-100" onClick={payMpesa} disabled={Boolean(pendingMpesa) || loadingMpesa}>
                {loadingMpesa ? 'Processing…' : pendingMpesa ? 'Waiting for M-PESA…' : '📱 Pay with M-PESA'}
              </button>

              <hr />
              <label className="form-label">Cash Received (KES)</label>
              <input type="number" className="form-control mb-2" placeholder="0" value={cashPaid} onChange={e => setCashPaid(e.target.value)} />
              {cashPaid && Number(cashPaid) >= total && (
                <div className="change-display">Change due: <strong>KES {change.toLocaleString()}</strong></div>
              )}
              <button className="btn btn-primary btn-lg w-100 mt-2" onClick={payCash} disabled={loadingCash} title="Ctrl+Enter">
                {loadingCash ? 'Processing…' : '💵 Pay Cash'}
              </button>
              <button className="btn btn-outline-secondary w-100 mt-2" onClick={clearCart}>Clear Cart (Esc)</button>

              {user?.is_staff && (
                <>
                  <hr />
                  <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:6 }}>Staff: Void recent sale</div>
                  <VoidSale />
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Receipt */}
      {receipt && (
        <div className="col-12 mt-4">
          <div className="card">
            <div className="card-header">
              <span>Receipt {receipt.sale?.receipt_number}</span>
              <div style={{ display:'flex', gap:8 }}>
                <button className="btn btn-dark btn-sm" onClick={() => window.print()}>🖨 Print</button>
                <button className="btn btn-outline-secondary btn-sm" onClick={() => setReceipt(null)}>✕ Close</button>
              </div>
            </div>
            <div className="card-body">
              <div className="receipt-box">
                <img src={logo} className="receipt-logo" alt="Logo" />
                <h4>Qubits Cyber Services</h4>
                <p style={{ fontSize:13, color:'#555' }}>Cyber Services · Printing · Online Applications</p>
                <hr style={{ borderColor:'#ddd' }} />
                <p><strong>Receipt:</strong> {receipt.sale?.receipt_number}</p>
                <p><strong>Date:</strong> {receipt.date}</p>
                <p><strong>Cashier:</strong> {user?.username}</p>
                <p><strong>Payment:</strong> {receipt.method}</p>
                {receipt.mpesaReceipt && <p><strong>M-PESA:</strong> {receipt.mpesaReceipt}</p>}
                {receipt.phone && <p><strong>Phone:</strong> {receipt.phone}</p>}
                <table className="table table-sm" style={{ marginTop:16 }}>
                  <thead><tr><th>Service</th><th>Unit</th><th>Qty</th><th style={{ textAlign:'right' }}>Amount</th></tr></thead>
                  <tbody>
                    {receipt.items.map(item => (
                      <tr key={item.id}>
                        <td>{item.name}</td>
                        <td>KES {Number(item.price).toLocaleString()}</td>
                        <td>{item.quantity}</td>
                        <td style={{ textAlign:'right' }}>KES {(Number(item.price) * item.quantity).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <p style={{ textAlign:'right', fontWeight:700, fontSize:16 }}>Total: KES {receipt.total.toLocaleString()}</p>
                {receipt.amountPaid && (
                  <p style={{ textAlign:'right', fontSize:13 }}>
                    Cash: KES {Number(receipt.amountPaid).toLocaleString()} | Change: KES {Number(receipt.changeDue).toLocaleString()}
                  </p>
                )}
                <p style={{ textAlign:'center', marginTop:24, fontSize:13, color:'#777' }}>Thank you for choosing Qubits!</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        .cat-section { margin-bottom: 8px; }
        .cat-header { width:100%; display:flex; align-items:center; gap:8px; background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius); padding:8px 12px; cursor:pointer; transition:background 0.15s; }
        .cat-header:hover { background:var(--surface3); }
        .cat-label { font-size:12px; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.06em; flex:1; text-align:left; }
        .cat-count { font-size:11px; background:var(--surface3); color:var(--text-muted); border-radius:20px; padding:1px 7px; }
        .cat-chevron { font-size:12px; color:var(--text-muted); }
        .service-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; padding:8px 0 4px; }
        .total-row { display:flex; justify-content:space-between; align-items:center; padding:12px 0; }
        .change-display { background:rgba(0,214,143,0.1); border:1px solid rgba(0,214,143,0.25); border-radius:8px; padding:8px 12px; font-size:14px; color:var(--accent); margin-bottom:8px; }
        .mpesa-spinner { width:18px; height:18px; border:2px solid rgba(255,165,2,0.3); border-top-color:var(--warn); border-radius:50%; animation:spin 0.8s linear infinite; flex-shrink:0; }
        @keyframes spin { to { transform:rotate(360deg); } }
        @media (max-width:768px) {
          .cart-panel { position:sticky; top:64px; z-index:10; max-height:50vh; overflow-y:auto; }
          .service-grid { grid-template-columns:repeat(2,1fr); }
        }
      `}</style>
    </div>
  );
}

function VoidSale() {
  const [receiptNum, setReceiptNum] = useState('');
  const [loading, setLoading]       = useState(false);
  const submit = async () => {
    if (!receiptNum.trim()) return;
    setLoading(true);
    try {
      const sales = await api.get('/sales/?search=' + receiptNum.trim());
      const sale  = (sales.data?.results || sales.data || []).find(s => s.receipt_number === receiptNum.trim());
      if (!sale) { toast.warning('Sale not found.'); return; }
      await api.post(`/sales/${sale.id}/cancel/`);
      toast.success(`Sale ${receiptNum} cancelled.`);
      setReceiptNum('');
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Failed to cancel sale.');
    } finally { setLoading(false); }
  };
  return (
    <div style={{ display:'flex', gap:8 }}>
      <input className="form-control form-control-sm" placeholder="Receipt # e.g. QBS-XKM84721" value={receiptNum} onChange={e => setReceiptNum(e.target.value)} />
      <button className="btn btn-sm btn-outline-danger" onClick={submit} disabled={loading || !receiptNum}>
        {loading ? '…' : 'Void'}
      </button>
    </div>
  );
}
