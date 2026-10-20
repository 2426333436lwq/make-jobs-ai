import React from 'react';

const PLATFORMS = [
  { value: 'boss', label: 'BOSS直聘' },
  { value: 'zhaopin', label: '智联招聘' },
  { value: 'liepin', label: '猎聘' },
  { value: '51job', label: '51job' },
  { value: 'yingjiesheng', label: '应届生求职' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'other', label: '其他' },
];

export default function JobForm({ jobForm, setJobForm, onSubmit, busy, message, error, parsedFields }) {
  const handleChange = (field) => (e) => {
    setJobForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  return (
    <div className="card">
      <h3>导入职位</h3>
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}

      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label>平台</label>
          <select value={jobForm.source_platform} onChange={handleChange('source_platform')}>
            <option value="">选择平台</option>
            {PLATFORMS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>职位链接（可选）</label>
          <input
            type="url"
            value={jobForm.source_url}
            onChange={handleChange('source_url')}
            placeholder="https://..."
          />
        </div>

        <div className="form-group">
          <label>职位描述原文</label>
          <textarea
            value={jobForm.raw_text}
            onChange={handleChange('raw_text')}
            rows={8}
            placeholder="粘贴职位描述原文..."
          />
        </div>

        {parsedFields && (
          <div className="parsed-preview">
            <h4>解析结果预览</h4>
            <div className="preview-item">
              <strong>岗位：</strong>
              {parsedFields.job_title || '未识别'}
            </div>
            <div className="preview-item">
              <strong>公司：</strong>
              {parsedFields.company_name || '未识别'}
            </div>
            <div className="preview-item">
              <strong>城市：</strong>
              {parsedFields.city || '未识别'}
            </div>
            <div className="preview-item">
              <strong>薪资：</strong>
              {parsedFields.salary_range || '未识别'}
            </div>
          </div>
        )}

        <button type="submit" disabled={busy}>
          {busy ? '导入中...' : '导入职位'}
        </button>
      </form>
    </div>
  );
}
