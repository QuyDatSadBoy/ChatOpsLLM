'use client';

const MODELS = [
  { value: 'gemini-flash', label: 'Gemini Flash (Google)' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (OpenAI)' },
  { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku (Anthropic)' },
  { value: 'meta-llama/Meta-Llama-3-8B-Instruct', label: 'Llama 3 8B (Self-hosted)' },
];

interface Props {
  model: string;
  onModelChange: (m: string) => void;
  onClose: () => void;
}

export default function SettingsPanel({ model, onModelChange, onClose }: Props) {
  return (
    <div className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-slate-700">Settings</h2>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">
          ×
        </button>
      </div>
      <label htmlFor="model-select" className="block text-sm text-slate-600 mb-1">Model</label>
      <select
        id="model-select"
        aria-label="Select LLM model"
        value={model}
        onChange={(e) => onModelChange(e.target.value)}
        className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
      >
        {MODELS.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
    </div>
  );
}
