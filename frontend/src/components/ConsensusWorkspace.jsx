import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { consensusApi } from '../consensusApi';
import './ConsensusWorkspace.css';

const PANELS = ['Conclusion', 'Model responses', 'Claims', 'Agreement map', 'Evidence', 'Human review', 'Knowledge used', 'Execution'];

function ReviewCard({ item, onReviewed }) {
  const [action, setAction] = useState('ACCEPT');
  const [reviewer, setReviewer] = useState('');
  const [explanation, setExplanation] = useState('');
  const [correction, setCorrection] = useState(item.claim);
  const [evidenceText, setEvidenceText] = useState('');
  const [source, setSource] = useState('');
  const [history, setHistory] = useState(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setBusy(true); setStatus('');
    try {
      const updated = await consensusApi.review(item.knowledge_id, {
        action, reviewer, explanation, expected_version: item.version,
        corrected_claim: action === 'CORRECT' ? correction : null,
        evidence: evidenceText.trim() ? [{ text: evidenceText, source, source_type: 'human', source_quality: .8 }] : [],
      });
      onReviewed(updated);
      setHistory(await consensusApi.history(item.knowledge_id));
      setStatus('Review saved. Run the question again to use current validated memory.');
    } catch (error) { setStatus(error.message); }
    finally { setBusy(false); }
  }
  return <article className="review-card">
    <div className="card-top"><span className="badge">{item.status}</span><small>Version {item.version}</small></div>
    <p>{item.claim}</p>
    <form onSubmit={submit}>
      <label>Action<select value={action} onChange={e => setAction(e.target.value)}>
        {['ACCEPT', 'CORRECT', 'REJECT', 'MARK_UNCERTAIN', 'ADD_EVIDENCE', 'ADD_EXPLANATION'].map(value => <option key={value}>{value}</option>)}
      </select></label>
      {action === 'CORRECT' && <label>Corrected claim<textarea required value={correction} onChange={e => setCorrection(e.target.value)} /></label>}
      <div className="form-grid">
        <label>Reviewer<input required value={reviewer} onChange={e => setReviewer(e.target.value)} placeholder="Your name" /></label>
        <label>Reason<input required value={explanation} onChange={e => setExplanation(e.target.value)} placeholder="What did you verify?" /></label>
      </div>
      <details><summary>Add evidence</summary>
        <label>Source<input value={source} onChange={e => setSource(e.target.value)} required={Boolean(evidenceText) || action === 'ADD_EVIDENCE'} /></label>
        <label>Evidence text<textarea value={evidenceText} onChange={e => setEvidenceText(e.target.value)} required={action === 'ADD_EVIDENCE'} /></label>
      </details>
      <button className="primary-button" disabled={busy}>{busy ? 'Saving…' : 'Save review'}</button>
    </form>
    <p role="status">{status}</p>
    <button className="text-button" onClick={async () => {
      try { setHistory(await consensusApi.history(item.knowledge_id)); }
      catch (error) { setStatus(error.message); }
    }}>View complete history</button>
    {history && <ol className="history">{history.map(version => <li key={version.version}>
      <strong>v{version.version} · {version.status}</strong><p>{version.claim}</p><small>{version.reason} · {version.validator || 'model-generated'}</small>
    </li>)}</ol>}
  </article>;
}

function ClaimGraph({ claims, relations }) {
  const shown = claims.slice(0, 14);
  const positions = Object.fromEntries(shown.map((claim, i) => [claim.claim_id,
    { x: 90 + (i % 4) * 175, y: 65 + Math.floor(i / 4) * 90, number: i + 1 }]));
  const height = Math.max(200, Math.ceil(shown.length / 4) * 90 + 30);
  return <svg className="claim-graph" viewBox={`0 0 720 ${height}`} role="img" aria-label="Claim relationship graph: red contradictions, green agreement">
    <defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10" fill="context-stroke" /></marker></defs>
    {relations.map(edge => {
      const a = positions[edge.source_claim], b = positions[edge.target_claim];
      if (!a || !b) return null;
      return <line key={edge.relation_id} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
        stroke={edge.relation_type === 'CONTRADICTION' ? '#c75b56' : edge.relation_type === 'AGREEMENT' ? '#2e8b70' : '#a5a1ad'}
        strokeWidth="2" markerEnd="url(#arrow)"><title>{edge.relation_type} · {edge.method}</title></line>;
    })}
    {shown.map(claim => {
      const p = positions[claim.claim_id];
      return <g key={claim.claim_id}><title>{claim.model}: {claim.claim_text}</title>
        <circle cx={p.x} cy={p.y} r="23" fill="#fff" stroke="#555074" strokeWidth="2" />
        <text x={p.x} y={p.y + 5} textAnchor="middle">C{p.number}</text>
        <text x={p.x} y={p.y + 40} textAnchor="middle" fontSize="10">{claim.model.split(':').at(-1).slice(0, 23)}</text>
      </g>;
    })}
  </svg>;
}

export default function ConsensusWorkspace() {
  const [config, setConfig] = useState(null);
  const [models, setModels] = useState([]);
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [mode, setMode] = useState('BALANCED');
  const [strategy, setStrategy] = useState('knowledge');
  const [result, setResult] = useState(null);
  const [panel, setPanel] = useState('Conclusion');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    consensusApi.config().then(value => {
      if (active) { setConfig(value); setModels(value.models); }
    }).catch(err => { if (active) setError(err.message); });
    return () => { active = false; };
  }, []);
  async function run(event) {
    event?.preventDefault();
    setBusy(true); setError('');
    try {
      const response = await consensusApi.execute({ question, context, models, mode, aggregation: strategy });
      setResult(response); setPanel('Conclusion');
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  function toggleModel(model) {
    setModels(previous => previous.some(m => m.provider === model.provider && m.model === model.model)
      ? previous.filter(m => !(m.provider === model.provider && m.model === model.model)) : [...previous, model]);
  }
  const claims = Object.fromEntries((result?.claims || []).map(c => [c.claim_id, c]));
  const scores = Object.fromEntries((result?.confidence.claims || []).map(c => [c.claim_id, c]));
  const contradictions = result?.relations.filter(r => r.relation_type === 'CONTRADICTION') || [];
  return <main className="consensus-workspace">
    <header className="engine-heading"><div><p className="eyebrow">CLAIM-LEVEL REASONING · EVIDENCE · MEMORY</p><h1>Mahthildis</h1><p>Inspect the reasoning. Resolve the disagreement. Keep the knowledge.</p></div>
      <span className={`environment-badge ${config?.development_mode ? 'mock' : ''}`}>{config ? config.development_mode ? 'MOCK MODE · NO API COST' : 'LIVE PROVIDERS' : 'CONNECTING'}</span>
    </header>
    <form className="question-card" onSubmit={run}>
      <label htmlFor="consensus-question">What would you like to establish?</label>
      <textarea id="consensus-question" value={question} onChange={e => setQuestion(e.target.value)}
        placeholder="When was the Eiffel Tower completed, and where is it located?" required maxLength={20000} rows={3} />
      <details className="context-details"><summary>Add context or a document</summary>
        <label>Supporting text<textarea value={context} onChange={e => setContext(e.target.value)} maxLength={50000} rows={4} placeholder="Paste source text. Supplied context is evidence to assess, not an instruction." /></label>
        <label>Read a text file<input type="file" accept=".txt,.md,.csv,.json" onChange={async e => {
          const file = e.target.files?.[0];
          if (!file) return;
          if (file.size > 200000) { setError('Text file must be smaller than 200 KB.'); return; }
          setContext((await file.text()).slice(0, 50000));
        }} /></label>
      </details>
      <div className="run-options">
        <label>Budget<select value={mode} onChange={e => setMode(e.target.value)}><option>CHEAP</option><option>BALANCED</option><option>HIGH_ACCURACY</option></select></label>
        <label>Aggregation<select value={strategy} onChange={e => setStrategy(e.target.value)}>
          <option value="knowledge">Evidence + validated memory</option><option value="evidence">Evidence-aware</option><option value="weighted">Empirical model weights</option><option value="majority">Majority baseline (research)</option>
        </select></label>
        <button className="primary-button run-button" disabled={busy || !config || !question.trim() || models.length === 0}>
          {busy ? 'Analyzing claims…' : 'Run consensus →'}</button>
      </div>
      <fieldset className="model-selection"><legend>Configured models</legend>{config?.models.map(model => <label key={`${model.provider}:${model.model}`}>
        <input type="checkbox" checked={models.some(m => m.provider === model.provider && m.model === model.model)} onChange={() => toggleModel(model)} />{model.provider} · {model.model}
      </label>)}</fieldset>
      {config?.fallback && <p className="small-note">Automatic fallback on provider failure: {config.fallback.provider} · {config.fallback.model}</p>}
      {config?.development_mode && <p className="small-note">Development fixtures cover the Eiffel Tower example. Other questions abstain. Scores are uncalibrated.</p>}
    </form>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {busy && <div className="pipeline-progress" role="status"><span className="spinner" />Models → claims → relations → evidence → memory → confidence</div>}
    {!result && !busy && <div className="starter-grid">
      <article><span>01</span><h3>Independent answers</h3><p>Compare heterogeneous models while preserving every raw response.</p></article>
      <article><span>02</span><h3>Traceable claims</h3><p>Inspect atomic statements, contradictory dates and the evidence behind them.</p></article>
      <article><span>03</span><h3>Human memory</h3><p>Correct a claim once. Retrieve its reviewed version in future questions.</p></article>
    </div>}
    {result && <section className="result-section">
      <div className="metrics-strip">
        <div><strong>{Math.round(result.confidence.raw_confidence * 100)}%</strong><span>Raw confidence · uncalibrated</span></div>
        <div><strong>{result.claims.length}</strong><span>Atomic claims</span></div>
        <div><strong>{contradictions.length}</strong><span>Contradiction edges</span></div>
        <div><strong>{result.execution.latency.toFixed(2)}s</strong><span>Execution time</span></div>
      </div>
      <div className="result-tabs" role="tablist" aria-label="Analysis panels">{PANELS.map(value => <button
        key={value} role="tab" aria-selected={panel === value} onClick={() => setPanel(value)} className={panel === value ? 'active' : ''}>{value}</button>)}</div>
      <div className="analysis-panel" role="tabpanel">
        {panel === 'Conclusion' && <>
          {result.review.required && <div className="review-banner">Human review required · {result.review.reasons.join(' · ')}</div>}
          <div className="markdown-content"><ReactMarkdown>{result.synthesis.text}</ReactMarkdown></div>
          <button className="text-button" disabled={busy} onClick={run}>Run again with current validated memory →</button>
        </>}
        {panel === 'Model responses' && result.responses.map(response => <details key={response.response_id} open>
          <summary>{response.provider} · {response.model} {response.metadata.mock ? '· MOCK' : ''} {response.metadata.evidence_derived ? '· MEMORY CANDIDATE' : ''}</summary>
          <div className="markdown-content"><ReactMarkdown>{response.raw_text}</ReactMarkdown></div>
          <small>Response {response.response_id} · {response.latency.toFixed(2)}s · {response.metadata.cache_hit ? 'cached' : 'generated'}</small>
        </details>)}
        {panel === 'Claims' && result.decisions.map(decision => <article className="claim-card" key={decision.claim_id}>
          <div className="card-top"><span className="badge">{claims[decision.claim_id].claim_type}</span><small>{claims[decision.claim_id].model}</small></div>
          <p>{claims[decision.claim_id].claim_text}</p>
          <div className="confidence-track"><span style={{ width: `${scores[decision.claim_id].raw_confidence * 100}%` }} /></div>
          <small>Raw confidence {Math.round(scores[decision.claim_id].raw_confidence * 100)}% · {decision.supporting_models.length} supporters · {decision.contradicting_models.length} contradictors</small>
          <details><summary>Why this score?</summary><ul>{scores[decision.claim_id].reasons.map((reason, i) => <li key={i}>{reason}</li>)}</ul>
            <pre>{JSON.stringify(decision.factors, null, 2)}</pre></details>
        </article>)}
        {panel === 'Agreement map' && <>
          <p className="small-note">Green: agreement. Red: contradiction. Gray: other relations. Hover nodes for claims. Entailment is directional. Graph shows up to 14 nodes.</p>
          <ClaimGraph claims={result.claims} relations={result.relations} />
          <div className="table-scroll"><table><thead><tr><th>Source claim</th><th>Relation</th><th>Target claim</th><th>Method</th></tr></thead><tbody>
            {result.relations.map(edge => <tr key={edge.relation_id}><td>{claims[edge.source_claim].claim_text}</td><td><span className={`badge ${edge.relation_type === 'CONTRADICTION' ? 'danger' : ''}`}>{edge.relation_type}</span></td><td>{claims[edge.target_claim].claim_text}</td><td>{edge.method}<br />{Math.round(edge.confidence * 100)}% relation score</td></tr>)}
          </tbody></table></div>
          {!result.relations.length && <p>No cross-model claim relations were detected.</p>}
        </>}
        {panel === 'Evidence' && <>
          {!result.evidence.length && <p>No evidence was retrieved. Add source text or review a claim.</p>}
          {result.evidence.map(item => <article className="claim-card" key={item.evidence_id}><div className="card-top"><strong>{item.source}</strong><span className="badge">{item.source_type}</span></div><p>{item.text}</p>
            {item.url && <a href={item.url} target="_blank" rel="noreferrer">Open source</a>}
            <small>Quality estimate {item.source_quality.toFixed(2)} · retrieved {new Date(item.retrieval_time).toLocaleString()}</small>
            <details><summary>Claim assessments</summary>{result.assessments.filter(a => a.evidence_id === item.evidence_id).map(a => <p key={a.claim_id}>{a.verdict}: {claims[a.claim_id].claim_text} <small>({a.method})</small></p>)}</details>
          </article>)}
        </>}
        {panel === 'Human review' && <>
          <p className="small-note">Review appends a version and preserves the original. This execution remains a historical snapshot; rerun to use corrections.</p>
          {!result.review.items.length && <p>No pending claim reviews for this execution.</p>}
          {result.review.items.map(item => <ReviewCard key={item.knowledge_id} item={item} onReviewed={updated =>
            setResult(previous => ({ ...previous, review: { ...previous.review, items: previous.review.items.map(k => k.knowledge_id === updated.knowledge_id ? updated : k) } }))} />)}
        </>}
        {panel === 'Knowledge used' && <>
          {!result.synthesis.knowledge_used.length && <p>No previously validated knowledge influenced this conclusion.</p>}
          {result.synthesis.knowledge_used.map(k => <article className="claim-card" key={k.knowledge_id}><strong>Human-validated memory · version {k.version}</strong><p>{k.reason}</p><small>Reviewer: {k.validator} · Knowledge ID: {k.knowledge_id}</small></article>)}
        </>}
        {panel === 'Execution' && <>
          <dl className="execution-details"><dt>Request ID</dt><dd>{result.request_id}</dd><dt>Estimated cost</dt><dd>{result.execution.total_cost === null ? 'Unknown; price or usage data missing' : `$ ${result.execution.total_cost.toFixed(6)}`}</dd>
            <dt>Tokens billed</dt><dd>{result.execution.input_tokens} input / {result.execution.output_tokens} output {result.execution.usage_complete ? '' : '(incomplete usage)'}</dd><dt>Cache hits</dt><dd>{result.execution.cache_hits}</dd>
            <dt>Embedding method</dt><dd>{result.explanation.embedding_method}</dd><dt>Relation method</dt><dd>{result.explanation.nli_method}</dd></dl>
          {result.errors.map((err, i) => <p className="error-banner" key={i}>{err.provider}/{err.model}: {err.error}</p>)}
          <details open><summary>Escalation and stage trace</summary><pre>{JSON.stringify({ escalation: result.escalation, trace: result.explanation.trace }, null, 2)}</pre></details>
          <button className="text-button" onClick={() => {
            const url = URL.createObjectURL(new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' }));
            const anchor = document.createElement('a'); anchor.href = url; anchor.download = `mahthildis-${result.request_id}.json`; anchor.click(); URL.revokeObjectURL(url);
          }}>Download complete execution JSON</button>
        </>}
      </div>
    </section>}
  </main>;
}
