import React from 'react';

export default function SettingsPanel({
  providers,
  settingsForm,
  setSettingsForm,
  availableModels,
  testingApi,
  testingResult,
  testStatus,
  onSave,
  onTest,
  onClose,
}) {
  const handleProviderChange = (e) => {
    const provider = e.target.value;
    setSettingsForm((prev) => ({
      ...prev,
      provider,
      api_base_url: providers[provider]?.base_url || '',
    }));
  };

  return (
    <div className="settings-overlay">
      <div className="settings-panel">
        <div className="settings-header">
          <h3>API 设置</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="settings-body">
          <div className="form-group">
            <label>AI 供应商</label>
            <select value={settingsForm.provider} onChange={handleProviderChange}>
              {Object.entries(providers).map(([key, p]) => (
                <option key={key} value={key}>
                  {p.name || key}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>API Base URL</label>
            <input
              type="url"
              value={settingsForm.api_base_url}
              onChange={(e) => setSettingsForm((prev) => ({ ...prev, api_base_url: e.target.value }))}
              placeholder="https://api.anthropic.com"
            />
          </div>

          <div className="form-group">
            <label>API Key</label>
            <input
              type="password"
              value={settingsForm.api_key}
              onChange={(e) => setSettingsForm((prev) => ({ ...prev, api_key: e.target.value }))}
              placeholder="sk-..."
            />
          </div>

          <div className="form-group">
            <label>模型</label>
            <select
              value={settingsForm.model}
              onChange={(e) => setSettingsForm((prev) => ({ ...prev, model: e.target.value }))}
            >
              <option value="">使用默认模型</option>
              {availableModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {testingResult && (
            <div className={`test-result ${testingResult.includes('成功') ? 'success' : 'error'}`}>
              {testingResult}
            </div>
          )}

          <div className="settings-actions">
            <button className="btn-secondary" onClick={onTest} disabled={testingApi}>
              {testingApi ? '测试中...' : '测试连接'}
            </button>
            <button className="btn-primary" onClick={onSave}>
              保存设置
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
