import React from 'react';

const STATUS_ROWS = [
  { key: 'OFF', label: '1. OFF', y: 35 },
  { key: 'SB',  label: '2. SB',  y: 75 },
  { key: 'D',   label: '3. D',   y: 115 },
  { key: 'ON',  label: '4. ON',  y: 155 },
];

export default function EldLogSheet({ sheet, dayIndex }) {
  const width = 800;
  const height = 195;
  const leftMargin = 65;
  const gridWidth = 700;
  const hourStep = gridWidth / 24;

  const getY = (s) => STATUS_ROWS.find(r => r.key === s)?.y || 35;
  const getX = (h) => leftMargin + h * hourStep;

  let pathD = '';
  sheet.events.forEach((ev, i) => {
    const x1 = getX(ev.start_hour);
    const x2 = getX(ev.end_hour);
    const y = getY(ev.status);

    if (i === 0) {
      pathD += `M ${x1} ${y} L ${x2} ${y}`;
    } else {
      pathD += ` L ${x1} ${y} L ${x2} ${y}`;
    }
  });

  return (
    <div style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '8px', padding: '16px', marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ margin: 0, fontSize: '15px', color: '#0f172a' }}>Day {dayIndex + 1} - {sheet.date}</h4>
        <div style={{ fontSize: '13px', color: '#475569' }}>
          OFF: <b>{sheet.totals.OFF}h</b> | SB: <b>{sheet.totals.SB}h</b> | D: <b>{sheet.totals.D}h</b> | ON: <b>{sheet.totals.ON}h</b> (24h Total)
        </div>
      </div>

      <svg width={width} height={height} style={{ width: '100%', height: 'auto', background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '4px' }}>
        {STATUS_ROWS.map(r => (
          <g key={r.key}>
            <text x="10" y={r.y + 4} fontSize="11" fontWeight="600" fill="#334155">{r.label}</text>
            <line x1={leftMargin} y1={r.y} x2={leftMargin + gridWidth} y2={r.y} stroke="#cbd5e1" strokeWidth="1" />
          </g>
        ))}

        {Array.from({ length: 25 }).map((_, h) => (
          <g key={h}>
            <line
              x1={leftMargin + h * hourStep}
              y1={20}
              x2={leftMargin + h * hourStep}
              y2={170}
              stroke={h % 4 === 0 ? '#94a3b8' : '#e2e8f0'}
              strokeWidth={h % 4 === 0 ? '1.5' : '1'}
            />
            {h < 24 && (
              <text x={leftMargin + h * hourStep + 2} y="15" fontSize="9" fill="#64748b">
                {h === 0 ? 'M' : h === 12 ? 'N' : h}
              </text>
            )}
          </g>
        ))}

        <path d={pathD} fill="none" stroke="#2563eb" strokeWidth="2.5" />
      </svg>

      <div style={{ marginTop: '12px', fontSize: '12px', color: '#334155' }}>
        <strong>Remarks: </strong>
        {sheet.events.map((e, idx) => (
          <span key={idx} style={{ marginRight: '12px' }}>
            [{e.start_hour}h-{e.end_hour}h] {e.status}: {e.remark}
          </span>
        ))}
      </div>
    </div>
  );
}
