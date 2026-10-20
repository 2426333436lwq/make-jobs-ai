import React from 'react';

const STATUS_LABELS = {
  draft: '草稿',
  pending: '待投递',
  applied: '已投递',
  rejected: '已拒绝',
  interview: '面试中',
  offer: '已录用',
};

const STATUS_COLORS = {
  draft: '#8c8c8c',
  pending: '#1890ff',
  applied: '#52c41a',
  rejected: '#ff4d4f',
  interview: '#722ed1',
  offer: '#fa8c16',
};

export default function ApplicationCard({ application, onConfirm }) {
  const status = application.status || 'draft';
  const statusLabel = STATUS_LABELS[status] || status;
  const statusColor = STATUS_COLORS[status] || '#8c8c8c';

  return (
    <div className="application-card">
      <div className="card-header">
        <span className="platform-badge">{application.platform}</span>
        <span className="status-badge" style={{ backgroundColor: statusColor }}>
          {statusLabel}
        </span>
      </div>

      <div className="card-body">
        {application.notes && <p className="recommendation">{application.notes}</p>}

        {application.target_url && (
          <a href={application.target_url} target="_blank" rel="noopener noreferrer" className="apply-link">
            查看职位详情 →
          </a>
        )}
      </div>

      <div className="card-footer">
        {status === 'draft' && (
          <button className="btn-primary" onClick={() => onConfirm(application.id)}>
            确认投递
          </button>
        )}
        <span className="created-time">
          {new Date(application.created_at).toLocaleDateString('zh-CN')}
        </span>
      </div>
    </div>
  );
}
