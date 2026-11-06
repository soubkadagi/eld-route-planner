import React, { useState } from 'react';
import axios from 'axios';
import RouteMap from './components/RouteMap';
import EldLogSheet from './components/EldLogSheet';

export default function App() {
  const [form, setForm] = useState({
    current_location: 'Chicago, IL',
    pickup_location: 'Indianapolis, IN',
    dropoff_location: 'Dallas, TX',
    cycle_used: 15
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const API_URL = process.env.REACT_APP_API_URL || 'https://eld-route-planner-2m3m.onrender.com';

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await axios.post(`${API_URL}/api/plan-trip/`, {
        current_location: form.current_location,
        pickup_location: form.pickup_location,
        dropoff_location: form.dropoff_location,
        cycle_used: Number(form.cycle_used)
      });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'Unable to calculate trip route.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '980px', margin: '24px auto', padding: '0 16px', fontFamily: 'sans-serif' }}>
      <header style={{ marginBottom: '20px' }}>
        <h2 style={{ margin: 0, color: '#0f172a' }}>FMCSA ELD Route & Log Generator</h2>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '14px' }}>
          Calculates compliant driving routes and generates FMCSA 24-hour log sheets.
        </p>
      </header>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', background: '#ffffff', padding: '16px', borderRadius: '8px', border: '1px solid #cbd5e1' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Current Location</label>
          <input name="current_location" value={form.current_location} onChange={handleChange} style={{ width: '90%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Pickup Location</label>
          <input name="pickup_location" value={form.pickup_location} onChange={handleChange} style={{ width: '90%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Dropoff Location</label>
          <input name="dropoff_location" value={form.dropoff_location} onChange={handleChange} style={{ width: '90%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>Cycle Used (Hrs)</label>
          <input type="number" step="0.5" name="cycle_used" value={form.cycle_used} onChange={handleChange} style={{ width: '90%', padding: '8px', border: '1px solid #cbd5e1', borderRadius: '4px' }} required />
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button type="submit" disabled={loading} style={{ width: '100%', padding: '9px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>
            {loading ? 'Processing...' : 'Generate Route & Logs'}
          </button>
        </div>
      </form>

      {error && <div style={{ color: '#b91c1c', background: '#fee2e2', padding: '10px', borderRadius: '6px', marginTop: '12px' }}>{error}</div>}

      {result && (
        <div style={{ marginTop: '24px' }}>
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
            <div style={{ flex: 1, padding: '12px', background: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: '12px', color: '#1e40af' }}>Total Miles</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{result.total_miles} mi</div>
            </div>
            <div style={{ flex: 1, padding: '12px', background: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: '12px', color: '#1e40af' }}>Est. Drive Time</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{result.total_driving_hours} hrs</div>
            </div>
            <div style={{ flex: 1, padding: '12px', background: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
              <div style={{ fontSize: '12px', color: '#1e40af' }}>Cycle Remaining</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{result.cycle_remaining} hrs</div>
            </div>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <h3 style={{ fontSize: '16px', color: '#334155' }}>Route Map</h3>
            <RouteMap geometry={result.route_geometry} />
          </div>

          <div>
            <h3 style={{ fontSize: '16px', color: '#334155' }}>Generated Driver Logs</h3>
            {result.daily_logs.map((sheet, idx) => (
              <EldLogSheet key={sheet.date} sheet={sheet} dayIndex={idx} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}