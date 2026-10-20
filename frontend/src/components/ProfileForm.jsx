import React from 'react';

export default function ProfileForm({ profileForm, setProfileForm, onSubmit, busy, message, error }) {
  const handleChange = (field) => (e) => {
    setProfileForm((prev) => ({ ...prev, [field]: e.target.value }));
  };

  return (
    <div className="card">
      <h3>简历资料</h3>
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}

      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label>姓名</label>
          <input
            type="text"
            value={profileForm.full_name}
            onChange={handleChange('full_name')}
            placeholder="请输入姓名"
          />
        </div>

        <div className="form-group">
          <label>求职意向</label>
          <input
            type="text"
            value={profileForm.job_intention}
            onChange={handleChange('job_intention')}
            placeholder="例如：AI 应用开发工程师"
          />
        </div>

        <div className="form-group">
          <label>自我评价</label>
          <textarea
            value={profileForm.self_evaluation}
            onChange={handleChange('self_evaluation')}
            rows={3}
            placeholder="简要描述您的职业定位和核心优势"
          />
        </div>

        <div className="form-group">
          <label>教育背景</label>
          <textarea
            value={profileForm.education_background}
            onChange={handleChange('education_background')}
            rows={2}
            placeholder="学校：xxx | 时间：xxxx-xxxx | 学历：xxx"
          />
        </div>

        <div className="form-group">
          <label>实习经历</label>
          <textarea
            value={profileForm.internship_experiences}
            onChange={handleChange('internship_experiences')}
            rows={4}
            placeholder="公司：xxx | 角色：xxx | 时间：xxxx-xxxx | 总结：xxx | 技能：xxx | 亮点：xxx"
          />
        </div>

        <div className="form-group">
          <label>项目经历</label>
          <textarea
            value={profileForm.project_experiences}
            onChange={handleChange('project_experiences')}
            rows={4}
            placeholder="项目名：xxx | 角色：xxx | 时间：xxxx-xxxx | 总结：xxx | 技能：xxx | 亮点：xxx"
          />
        </div>

        <div className="form-group">
          <label>技能（逗号分隔）</label>
          <input
            type="text"
            value={profileForm.skills_text}
            onChange={handleChange('skills_text')}
            placeholder="Python, FastAPI, React, SQL"
          />
        </div>

        <button type="submit" disabled={busy}>
          {busy ? '保存中...' : '保存资料'}
        </button>
      </form>
    </div>
  );
}
