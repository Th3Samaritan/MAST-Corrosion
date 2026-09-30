'use client';

import { useEffect, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import {
  Activity,
  FlaskConical,
  BookOpen,
  Layers3,
  ArrowUpRight,
  ShieldCheck,
  Download,
  Upload,
  Save,
  Plus,
  ArrowRight,
  CircleHelp,
  FileText,
  Trash2,
  Check,
  Printer,
  AlertTriangle,
} from 'lucide-react';
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
  SidebarTrigger,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from '@/components/ui/alert-dialog';
import {
  Empty,
  EmptyHeader,
  EmptyTitle,
  EmptyDescription,
} from '@/components/ui/empty';
import {
  calculate,
  example,
  methods,
  projectedThickness,
  ENGINE_VERSION,
} from '@/lib/corrosion';
import type { Draft, Result, Method } from '@/lib/corrosion';
import { restoreSnapshots, markdownReport } from '@/lib/reports';
import type { Snapshot } from '@/lib/reports';
import { Evidence } from './evidence';
import { CloudWorkspace } from './cloud-workspace';
import { GalvanicResearch } from './galvanic-research';
import { calculateAssessment, apiUrl } from '@/lib/cloud';

const storageKey = 'mast.assessments.v1';
const navigation = [
  { Icon: Activity, label: 'Assessment', id: 'assessment' },
  { Icon: Layers3, label: 'Saved comparisons', id: 'saved' },
  { Icon: FlaskConical, label: 'Galvanic research', id: 'galvanic' },
  { Icon: BookOpen, label: 'Methods & evidence', id: 'evidence' },
];
const fmt = (n: number, d = 3) =>
  n === 0
    ? '0'
    : Math.abs(n) < 0.001
      ? n.toExponential(2)
      : n.toLocaleString('en-US', {
          maximumFractionDigits: d,
          minimumFractionDigits: d,
        });
function download(name: string, body: string, type: string) {
  const url = URL.createObjectURL(new Blob([body], { type }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function Pick({
  label,
  value,
  items,
  onChange,
}: {
  label: string;
  value: string;
  items: Record<string, string>;
  onChange: (v: string) => void;
}) {
  return (
    <div className="field">
      <span>{label}</span>
      <Select
        value={value}
        onValueChange={(v) => {
          if (v) onChange(v);
        }}
      >
        <SelectTrigger aria-label={label} className="picker">
          <SelectValue>{items[value]}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {Object.entries(items).map(([v, t]) => (
            <SelectItem key={v} value={v}>
              {t}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
function Forecast({ r }: { r: Result }) {
  const canForecast = r.thresholdState === 'conditional';
  const points = Array.from({ length: 5 }, (_, i) => (i * r.horizon) / 4);
  const upper = Math.max(r.latest * 1.1, r.minimum * 1.15, 0.01);
  const y = (n: number) => 205 - (170 * n) / upper;
  const x = (n: number) => 55 + (480 * n) / r.horizon;
  return (
    <div className="panel forecast-panel">
      <div className="chart-heading">
        <div>
          <h2>Thickness outlook</h2>
          <p>
            Constant-rate scenario · {r.horizon} years from latest measurement
          </p>
        </div>
        <span className="tag">mm</span>
      </div>
      {canForecast ? (
        <>
          <svg
            className="forecast-chart"
            viewBox="0 0 580 245"
            role="img"
            aria-label={`Conditional thickness forecast from ${r.latest} millimeters to ${fmt(projectedThickness(r, r.horizon))} millimeters over ${r.horizon} years. Shaded area is sensitivity, not predictive confidence.`}
          >
            {[0, 1, 2, 3, 4].map((i) => (
              <g key={i}>
                <line
                  x1="55"
                  y1={y((upper * i) / 4)}
                  x2="535"
                  y2={y((upper * i) / 4)}
                  stroke="#e3eaf1"
                />
                <text x="42" y={y((upper * i) / 4) + 4} textAnchor="end">
                  {fmt((upper * i) / 4, 1)}
                </text>
              </g>
            ))}
            <polygon
              points={[
                ...points.map(
                  (t) => `${x(t)},${y(projectedThickness(r, t, r.range[0]))}`,
                ),
                ...points
                  .slice()
                  .reverse()
                  .map(
                    (t) => `${x(t)},${y(projectedThickness(r, t, r.range[1]))}`,
                  ),
              ].join(' ')}
              fill="#008b9c"
              opacity=".12"
            />
            <line
              x1="55"
              y1={y(r.minimum)}
              x2="535"
              y2={y(r.minimum)}
              stroke="#c84620"
              strokeDasharray="6 5"
            />
            <polyline
              points={points
                .map((t) => `${x(t)},${y(projectedThickness(r, t))}`)
                .join(' ')}
              fill="none"
              stroke="#008599"
              strokeWidth="3"
            />
            {points.map((t) => (
              <g key={t}>
                <circle
                  cx={x(t)}
                  cy={y(projectedThickness(r, t))}
                  r="4"
                  fill="#008599"
                  stroke="white"
                  strokeWidth="2"
                />
                <text x={x(t)} y="231" textAnchor="middle">
                  {fmt(t, 1)} y
                </text>
              </g>
            ))}
          </svg>
          <div className="chart-legend">
            <span>
              <i />
              Rate scenario
            </span>
            <span>
              <i className="band" />
              {r.rangeLabel}
            </span>
            <span>
              <i className="minimum" />
              Supplied minimum
            </span>
          </div>
          <p className="chart-note">
            The shaded range excludes future changes in exposure and model
            error. Thickness is floored at zero.
          </p>
          <details className="data-details">
            <summary>View forecast values</summary>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Years</TableHead>
                  <TableHead>Thickness · mm</TableHead>
                  <TableHead>Range · mm</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {points.map((t) => (
                  <TableRow key={t}>
                    <TableCell>{fmt(t, 1)}</TableCell>
                    <TableCell>{fmt(projectedThickness(r, t))}</TableCell>
                    <TableCell>
                      {fmt(projectedThickness(r, t, r.range[1]))}–
                      {fmt(projectedThickness(r, t, r.range[0]))}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </details>
        </>
      ) : (
        <div className="forecast-empty">
          <AlertTriangle />
          <h3>
            {r.thresholdState === 'reached'
              ? 'Supplied minimum reached'
              : 'Forecast unresolved'}
          </h3>
          <p>
            {r.thresholdState === 'reached'
              ? 'The latest thickness has no positive margin above your minimum. Refer this assessment for engineering review.'
              : 'The entered evidence does not resolve a positive loss rate. Further consistent measurements are needed before extrapolating.'}
          </p>
        </div>
      )}
    </div>
  );
}
export default function Home() {
  const [view, setView] = useState('assessment');
  const [draft, setDraft] = useState<Draft>({ ...example });
  const [active, setActive] = useState<Snapshot | null>(null);
  const [preview, setPreview] = useState<Result | null>(() =>
    calculate(example),
  );
  const [saved, setSaved] = useState<Snapshot[]>([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [importing, setImporting] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const revision = useRef(0);
  const [confirm, setConfirm] = useState<string | null>(null);
  const [hasStorage, setHasStorage] = useState(true);
  const csvRef = useRef<HTMLInputElement>(null),
    reportRef = useRef<HTMLInputElement>(null);
  const currentRef = useRef({ draft, active, preview });
  useEffect(() => {
    currentRef.current = { draft, active, preview };
  }, [draft, active, preview]);
  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) setSaved(restoreSnapshots(JSON.parse(raw)));
    } catch {
      setHasStorage(false);
      setError(
        'Saved assessments could not be read. Existing browser data has been preserved. Export new reports as files.',
      );
    }
  }, []);
  useEffect(() => {
    const context = (
      document as Document & {
        modelContext?: {
          registerTool: (
            tool: unknown,
            options: { signal: AbortSignal },
          ) => unknown;
        };
      }
    ).modelContext;
    if (!context?.registerTool) return;
    const controller = new AbortController();
    try {
      Promise.resolve(
        context.registerTool(
          {
            name: 'calculate_current_corrosion_assessment',
            title: 'Calculate current corrosion assessment',
            description:
              'Validate the currently visible assessment inputs and update its result. Does not save or certify it.',
            inputSchema: {
              type: 'object',
              properties: {},
              additionalProperties: false,
            },
            annotations: { readOnlyHint: false, untrustedContentHint: true },
            execute: async (input: unknown) => {
              if (
                !input ||
                typeof input !== 'object' ||
                Array.isArray(input) ||
                Object.keys(input).length
              )
                throw new Error('Expected an empty object.');
              const rev = revision.current;
              const s = await calculateAssessment(currentRef.current.draft);
              if (rev !== revision.current)
                throw new Error(
                  'Inputs changed during calculation. Recalculate.',
                );
              flushSync(() => {
                setActive(s);
                setPreview(s.result);
                setError('');
                setView('assessment');
              });
              return {
                rate_mm_year: s.result.rate,
                range: s.result.range,
                status: s.status,
                provenance: s.draft.provenance,
                warnings: s.result.warnings,
              };
            },
          },
          { signal: controller.signal },
        ),
      ).catch(() => {});
    } catch {
      /* Optional API unavailable; normal interface remains usable. */
    }
    return () => controller.abort();
  }, []);
  function edit(key: keyof Draft, value: string) {
    revision.current++;
    setDraft((d) => ({ ...d, [key]: value }));
    setActive(null);
    setPreview(null);
    setError('');
    setMessage('');
  }
  async function run() {
    const rev = revision.current;
    setCalculating(true);
    try {
      const s = await calculateAssessment(draft);
      if (rev !== revision.current) return null;
      setActive(s);
      setPreview(s.result);
      setError('');
      setMessage(
        'Calculation complete. Review the basis before saving or exporting.',
      );
      return s;
    } catch (e) {
      setActive(null);
      setPreview(null);
      setError(e instanceof Error ? e.message : 'Unable to calculate.');
      return null;
    } finally {
      setCalculating(false);
    }
  }
  function persist(next: Snapshot[]) {
    if (!hasStorage) {
      setError('Browser storage is unavailable. Export a report file instead.');
      return false;
    }
    try {
      localStorage.setItem(storageKey, JSON.stringify(next));
      setSaved(next);
      return true;
    } catch {
      setError(
        'Could not save on this device. Storage may be full or unavailable; export a file instead.',
      );
      return false;
    }
  }
  async function save() {
    const s = active || (await run());
    if (!s) return;
    if (saved.some((x) => x.id === s.id)) {
      setMessage('This assessment is already saved on this device.');
      return;
    }
    if (saved.length >= 100) {
      setError(
        'The 100-assessment device limit has been reached. Export and remove older assessments.',
      );
      return;
    }
    if (persist([s, ...saved]))
      setMessage(
        'Assessment saved on this device. It is not synced or backed up.',
      );
  }
  async function exportReport(format: 'json' | 'md') {
    const s = active || (await run());
    if (!s) return;
    download(
      `mast-assessment-${s.id.slice(0, 8)}.${format}`,
      format === 'json' ? JSON.stringify(s, null, 2) : markdownReport(s),
      format === 'json' ? 'application/json' : 'text/markdown',
    );
    setMessage('Report file prepared. Review status remains unreviewed.');
  }
  async function importFile(file: File | undefined, type: 'csv' | 'json') {
    if (!file) return;
    if (file.size > 200000) {
      setError('File exceeds the 200 KB limit.');
      return;
    }
    setImporting(true);
    setError('');
    try {
      const raw = await file.text();
      if (type === 'csv') {
        edit('readings', raw);
        setDraft((d) => ({
          ...d,
          method: 'thickness',
          source: file.name,
          provenance: 'measurement',
        }));
        setMessage(
          'CSV staged. Confirm one inspection location, units and provenance, then calculate.',
        );
      } else {
        const s = restoreSnapshots([JSON.parse(raw)])[0];
        revision.current++;
        setDraft(s.draft);
        setPreview(null);
        setActive(null);
        setView('assessment');
        setMessage(
          'Report inputs loaded. Recalculate with the current engine before saving.',
        );
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'File could not be imported.');
    } finally {
      setImporting(false);
      if (csvRef.current) csvRef.current.value = '';
      if (reportRef.current) reportRef.current.value = '';
    }
  }
  function reset() {
    revision.current++;
    setDraft({
      ...example,
      name: '',
      material: '',
      environment: '',
      source: '',
      provenance: 'measurement',
      readings: 'date,thickness_mm\n',
      density: '',
      equivalentWeight: '',
      current: '',
      resistance: '',
      betaA: '',
      betaC: '',
      loss: '',
      area: '',
      hours: '',
      latest: '',
      minimum: '',
      tolerance: '',
      sensitivity: '',
    });
    setPreview(null);
    setActive(null);
    setError('');
    setMessage('New assessment. Enter your evidence and material properties.');
    setView('assessment');
  }
  function field(
    key: keyof Draft,
    label: string,
    hint?: string,
    type = 'number',
  ) {
    return (
      <label className="field" key={key}>
        {label}
        <input
          type={type}
          step={type === 'number' ? 'any' : undefined}
          value={draft[key]}
          onChange={(e) => edit(key, e.target.value)}
          aria-describedby={hint ? `${key}-hint` : undefined}
        />
        {hint && <small id={`${key}-hint`}>{hint}</small>}
      </label>
    );
  }
  const r = preview;
  return (
    <SidebarProvider
      style={{ '--sidebar-width': '14.5rem' } as React.CSSProperties}
    >
      <a className="skip-link" href="#main-content">
        Skip to assessment
      </a>
      <Sidebar>
        <SidebarHeader>
          <div className="brand">
            <span className="brand-mark">M</span>
            <span>
              MAST<span className="brand-sub">CORROSION</span>
            </span>
          </div>
        </SidebarHeader>
        <SidebarContent>
          <div className="nav-label">ENGINEERING WORKSPACE</div>
          <SidebarMenu>
            {navigation.map(({ Icon, label, id }) => (
              <SidebarMenuItem key={id}>
                <SidebarMenuButton
                  onClick={() => setView(id)}
                  isActive={view === id}
                >
                  <Icon />
                  <span>{label}</span>
                  {id === 'saved' && (
                    <span className="nav-count">{saved.length}</span>
                  )}
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
          <div className="sidebar-note">
            <ShieldCheck size={20} />
            <b>Evidence before estimates.</b>
            <p>
              Explicit physics. Recorded assumptions. Results you can trace.
            </p>
          </div>
        </SidebarContent>
        <SidebarFooter>
          <span className="version">RESEARCH PREVIEW · v{ENGINE_VERSION}</span>
        </SidebarFooter>
      </Sidebar>
      <main id="main-content" className="workspace">
        <header className="topbar">
          <div className="inline">
            <SidebarTrigger />
            <span>
              Workspace <span className="slash">/</span>{' '}
              {navigation.find((n) => n.id === view)?.label}
            </span>
          </div>
          <span className="status-dot">
            {apiUrl ? 'Connected calculation API' : 'Local calculation mode'}
          </span>
        </header>
        <div className="content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">CORROSION INTELLIGENCE</div>
              <h1>
                {view === 'assessment'
                  ? 'Make metal loss measurable.'
                  : view === 'saved'
                    ? 'Evidence, side by side.'
                    : view === 'galvanic'
                      ? 'Explore galvanic interactions.'
                      : 'Understand every result.'}
              </h1>
              <p>
                {view === 'assessment'
                  ? 'From inspection evidence to a defensible corrosion forecast.'
                  : view === 'saved'
                    ? 'Private cloud snapshots and device-saved assessments.'
                    : view === 'galvanic'
                      ? 'Your trained model, material reference and training history.'
                      : 'The science, assumptions and validation behind MAST.'}
              </p>
            </div>
            <Button className="primary" onClick={() => setConfirm('new')}>
              <Plus />
              New assessment
            </Button>
          </div>
          <div role="status" aria-live="polite">
            {message && (
              <div className="feedback">
                <Check size={17} />
                {message}
              </div>
            )}
            {importing && <div className="notice">Reading your file…</div>}
          </div>
          {error && (
            <div className="error" role="alert">
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}
          <input
            ref={reportRef}
            type="file"
            accept=".json"
            className="sr-only"
            aria-label="Import assessment JSON"
            onChange={(e) => void importFile(e.target.files?.[0], 'json')}
          />
          {view === 'assessment' && (
            <>
              <div className="notice">
                <FlaskConical size={18} />
                <span>
                  {draft.provenance === 'example'
                    ? 'Illustrative example · Replace sample inputs with your measurements.'
                    : draft.provenance === 'assumed'
                      ? 'Assumed-input scenario · Results depend on the assumptions you supply.'
                      : 'User-supplied measurements · Verify measurement quality and applicability.'}{' '}
                  Field accuracy has not been validated.
                </span>
              </div>
              <div className="assessment-grid">
                <form
                  className="panel input-panel"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void run();
                  }}
                >
                  <div className="section-title">
                    <span className="step">01</span>
                    <h2>Assessment inputs</h2>
                    <Button
                      type="button"
                      variant="ghost"
                      className="help-button"
                      onClick={() => setView('evidence')}
                      aria-label="Read calculation guidance"
                    >
                      <CircleHelp size={18} />
                    </Button>
                  </div>
                  <Pick
                    label="Calculation method"
                    value={draft.method}
                    items={methods}
                    onChange={(v) => edit('method', v as Method)}
                  />
                  <Pick
                    label="Damage mechanism"
                    value={draft.mechanism}
                    items={{
                      uniform: 'Uniform metal loss',
                      pitting: 'Pitting / crevice / MIC',
                      galvanic: 'Galvanic forward prediction',
                      cracking: 'Cracking / erosion',
                      unknown: 'Not yet identified',
                    }}
                    onChange={(v) => edit('mechanism', v)}
                  />
                  {field(
                    'name',
                    'Asset / inspection location',
                    undefined,
                    'text',
                  )}
                  <div className="input-divider">
                    <span>MEASUREMENT BASIS</span>
                  </div>
                  {draft.method === 'thickness' ? (
                    <>
                      <label className="field">
                        Dated thickness readings
                        <textarea
                          value={draft.readings}
                          spellCheck={false}
                          onChange={(e) => edit('readings', e.target.value)}
                          aria-describedby="csv-help"
                        />
                        <small id="csv-help">
                          CSV: date,thickness_mm. One location, 2–1,000
                          readings, unique ISO dates. All readings enter the
                          fitted trend.
                        </small>
                      </label>
                      <div className="file-actions">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => csvRef.current?.click()}
                          disabled={importing}
                        >
                          <Upload />
                          Import CSV
                        </Button>
                        <button
                          type="button"
                          className="text-link"
                          onClick={() =>
                            download(
                              'thickness-template.csv',
                              'date,thickness_mm\n',
                              'text/csv',
                            )
                          }
                        >
                          Blank template <ArrowUpRight size={13} />
                        </button>
                      </div>
                      <input
                        ref={csvRef}
                        className="sr-only"
                        type="file"
                        accept=".csv,text/csv"
                        aria-label="Import thickness CSV"
                        onChange={(e) =>
                          void importFile(e.target.files?.[0], 'csv')
                        }
                      />
                      {field(
                        'tolerance',
                        'Absolute thickness tolerance · ±mm',
                        'Applied to each reading. Input bounds only; not predictive confidence.',
                      )}
                    </>
                  ) : (
                    <>
                      {draft.method === 'current' &&
                        field(
                          'current',
                          'Corrosion current density · µA/cm²',
                          'Use independently estimated corrosion current, not net open-circuit current.',
                        )}
                      {draft.method === 'lpr' && (
                        <>
                          {field(
                            'resistance',
                            'Polarization resistance · Ω·cm²',
                            'Area-normalized Rp. For resistance in Ω, multiply by exposed area in cm².',
                          )}
                          <div className="two-col">
                            {field('betaA', 'Anodic slope · mV/dec')}
                            {field('betaC', 'Cathodic slope · mV/dec')}
                          </div>
                          <p className="field-note">
                            Positive slope magnitudes from independent
                            characterization. LPR does not measure these slopes.
                          </p>
                        </>
                      )}
                      {draft.method === 'coupon' && (
                        <>
                          <div className="two-col">
                            {field('loss', 'Gross mass loss · mg')}
                            {field('cleaning', 'Cleaning correction · mg')}
                          </div>
                          <div className="two-col">
                            {field('area', 'Exposed area · cm²')}
                            {field('hours', 'Exposure duration · h')}
                          </div>
                        </>
                      )}
                      <div className="two-col">
                        {field('density', 'Density · g/cm³')}
                        {draft.method !== 'coupon' &&
                          field(
                            'equivalentWeight',
                            'Equivalent weight · g/equiv',
                          )}
                      </div>
                      <p className="field-note">
                        Use verified properties for your actual material.
                        Example values approximate iron dissolving as Fe²⁺, not
                        every steel alloy.
                      </p>
                      {field(
                        'latest',
                        'Latest asset thickness · mm',
                        'For a transferred lab/coupon rate, confirm that the asset exposure is representative.',
                      )}
                      {field(
                        'sensitivity',
                        'Rate sensitivity · ±%',
                        'User-selected scenario range, 0–100%. This is not statistical uncertainty.',
                      )}
                    </>
                  )}
                  <div className="input-divider">
                    <span>FORECAST CONDITIONS</span>
                  </div>
                  <div className="two-col">
                    {field('minimum', 'Supplied minimum · mm')}
                    {field('horizon', 'Horizon · years')}
                  </div>
                  <p className="field-note">
                    The minimum must come from a qualified assessment. MAST does
                    not calculate an allowable wall thickness.
                  </p>
                  <details className="evidence-details" open>
                    <summary>Material & provenance</summary>
                    {field('material', 'Material / grade', undefined, 'text')}
                    {field(
                      'environment',
                      'Exposure / operating conditions',
                      'Record temperature, medium, changes and other relevant conditions. Context is retained, not modeled as a rate multiplier.',
                      'text',
                    )}
                    <Pick
                      label="Input provenance"
                      value={draft.provenance}
                      items={{
                        example: 'Illustrative example',
                        measurement: 'User-supplied measurements',
                        assumed: 'Assumed scenario',
                      }}
                      onChange={(v) => edit('provenance', v)}
                    />
                    {field(
                      'source',
                      'Measurement source / reference',
                      undefined,
                      'text',
                    )}
                    {field('notes', 'Assessment notes', undefined, 'text')}
                  </details>
                  <Button
                    type="submit"
                    className="primary wide"
                    disabled={importing || calculating}
                  >
                    {calculating ? 'Calculating…' : 'Calculate corrosion rate'}{' '}
                    <ArrowRight />
                  </Button>
                </form>
                <section className="results" aria-label="Assessment results">
                  {r ? (
                    <>
                      <div className="rate-card">
                        <div className="rate-top">
                          <span className="eyebrow">
                            {r.rate < 0
                              ? 'SIGNED THICKNESS TREND'
                              : 'AVERAGE METAL LOSS'}
                          </span>
                          <span className="result-badge">
                            {draft.provenance === 'example'
                              ? 'EXAMPLE'
                              : 'UNREVIEWED'}
                          </span>
                        </div>
                        <div className="rate-number">
                          {fmt(r.rate)} <span>mm / year</span>
                        </div>
                        <div className="rate-sub">
                          {fmt(r.range[0])}–{fmt(r.range[1])} mm/year{' '}
                          <span>· {r.rangeLabel.toLowerCase()}</span>
                        </div>
                        <div className="rate-footer">
                          <span>{methods[r.method]}</span>
                          <span>Engine {r.version}</span>
                        </div>
                      </div>
                      <div className="metrics">
                        <div>
                          <span>Thickness margin</span>
                          <b>
                            {fmt(r.latest - r.minimum, 2)} <small>mm</small>
                          </b>
                          <p>Above your supplied minimum</p>
                        </div>
                        <div>
                          <span>Time to supplied minimum</span>
                          <b>
                            {r.yearsToMinimum === null
                              ? 'Unresolved'
                              : fmt(r.yearsToMinimum, 1)}{' '}
                            {r.yearsToMinimum !== null && <small>years</small>}
                          </b>
                          <p>
                            {r.thresholdState === 'reached'
                              ? 'Minimum already reached'
                              : 'Conditional · not safe service life'}
                          </p>
                        </div>
                      </div>
                      <Forecast r={r} />
                      <Tabs defaultValue="basis" className="panel detail-tabs">
                        <TabsList variant="line">
                          <TabsTrigger value="basis">
                            Calculation basis
                          </TabsTrigger>
                          <TabsTrigger value="limits">
                            Review notes ({r.warnings.length})
                          </TabsTrigger>
                          <TabsTrigger value="evidence">Evidence</TabsTrigger>
                        </TabsList>
                        <TabsContent value="basis">
                          <h3>{r.basis}</h3>
                          <div className="formula">{r.formula}</div>
                          <dl className="trace">
                            {r.trace.map((t) => (
                              <div key={t.label}>
                                <dt>{t.label}</dt>
                                <dd>{t.value}</dd>
                              </div>
                            ))}
                          </dl>
                          <p className="field-note">
                            Rate calculations are uniform-loss estimates.
                            Numerical correctness does not establish field
                            prediction accuracy.
                          </p>
                        </TabsContent>
                        <TabsContent value="limits">
                          <ul className="warnings">
                            {r.warnings.map((w) => (
                              <li key={w}>
                                <AlertTriangle size={15} />
                                <span>{w}</span>
                              </li>
                            ))}
                          </ul>
                        </TabsContent>
                        <TabsContent value="evidence">
                          <dl className="trace">
                            <div>
                              <dt>Material</dt>
                              <dd>{draft.material}</dd>
                            </div>
                            <div>
                              <dt>Environment</dt>
                              <dd>{draft.environment}</dd>
                            </div>
                            <div>
                              <dt>Source</dt>
                              <dd>{draft.source}</dd>
                            </div>
                            <div>
                              <dt>Provenance</dt>
                              <dd>{draft.provenance}</dd>
                            </div>
                            <div>
                              <dt>Review</dt>
                              <dd>
                                Unreviewed · requires independent engineering
                                review
                              </dd>
                            </div>
                          </dl>
                          {r.readings.length > 0 && (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Date</TableHead>
                                  <TableHead>Thickness · mm</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {r.readings.map((v) => (
                                  <TableRow key={v.date}>
                                    <TableCell>{v.date}</TableCell>
                                    <TableCell>{fmt(v.thickness)}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          )}
                        </TabsContent>
                      </Tabs>
                      <div className="output-actions">
                        <Button
                          disabled={calculating}
                          onClick={() => void save()}
                          variant="outline"
                        >
                          <Save />
                          Save on this device
                        </Button>
                        <Button
                          disabled={calculating}
                          onClick={() => void exportReport('md')}
                          variant="outline"
                        >
                          <FileText />
                          Export report
                        </Button>
                        <Button
                          disabled={calculating}
                          onClick={() => void exportReport('json')}
                          variant="outline"
                        >
                          <Download />
                          JSON
                        </Button>
                        <Button
                          disabled={calculating}
                          onClick={async () => {
                            const s = active || (await run());
                            if (s) window.print();
                          }}
                          variant="ghost"
                          aria-label="Print assessment"
                        >
                          <Printer />
                        </Button>
                      </div>
                      <p className="storage-note">
                        Saved records stay in this browser. Export files for
                        backup or independent review.
                      </p>
                      <div className="print-only">
                        <h2>Assessment evidence & limitations</h2>
                        <p>
                          {draft.name} · {draft.material} · {draft.source} ·
                          Provenance: {draft.provenance}
                        </p>
                        <p>{draft.environment}</p>
                        <p>{r.formula}</p>
                        {r.warnings.map((w) => (
                          <p key={w}>{w}</p>
                        ))}
                      </div>
                    </>
                  ) : (
                    <div className="panel pending">
                      <Activity />
                      <h2>
                        {draft.mechanism !== 'uniform'
                          ? 'Specialist model required'
                          : 'Ready when your evidence is.'}
                      </h2>
                      <p>
                        {draft.mechanism !== 'uniform'
                          ? 'This mechanism is outside the uniform-loss engine. MAST will not produce a rate from a metal pair or a damage label alone.'
                          : 'Enter measurements and calculate to see the rate, thickness scenario and review notes.'}
                      </p>
                      <div className="process-list">
                        <span>
                          01 <b>Record the measurement basis</b>
                        </span>
                        <span>
                          02 <b>Calculate in explicit units</b>
                        </span>
                        <span>
                          03 <b>Review, compare and export</b>
                        </span>
                      </div>
                    </div>
                  )}
                </section>
              </div>
            </>
          )}
          {view === 'saved' && (
            <>
              <CloudWorkspace
                draft={draft}
                onLoad={(s) => {
                  revision.current++;
                  setDraft({ ...s.draft });
                  setActive(null);
                  setPreview(s.result);
                  setView('assessment');
                  setMessage(
                    'Cloud inputs loaded and recalculated with the current engine.',
                  );
                  setError('');
                }}
              />
              <h2 className="local-heading">Saved on this device</h2>
              <div className="saved-toolbar">
                <div className="notice">
                  <Layers3 size={18} />
                  <span>
                    {saved.length} saved on this device · No cloud sync. All
                    records remain unreviewed.
                  </span>
                </div>
                <Button
                  variant="outline"
                  onClick={() => reportRef.current?.click()}
                  disabled={importing}
                >
                  <Upload />
                  Import report JSON
                </Button>
              </div>
              {saved.length === 0 ? (
                <Empty className="panel empty-state">
                  <EmptyHeader>
                    <Layers3 className="empty-icon" />
                    <EmptyTitle>No saved assessments yet</EmptyTitle>
                    <EmptyDescription>
                      Calculate an assessment and save it on this device to
                      compare rates and their evidence.
                    </EmptyDescription>
                  </EmptyHeader>
                  <Button
                    className="primary"
                    onClick={() => setView('assessment')}
                  >
                    Open assessment <ArrowRight />
                  </Button>
                </Empty>
              ) : (
                <>
                  <div className="panel">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Asset / location</TableHead>
                          <TableHead>Method</TableHead>
                          <TableHead>Rate · mm/year</TableHead>
                          <TableHead>Provenance</TableHead>
                          <TableHead>Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {saved.map((s) => (
                          <TableRow key={s.id}>
                            <TableCell>
                              <b>{s.draft.name}</b>
                              <small className="table-date">
                                {new Date(s.createdAt).toLocaleDateString()} ·
                                unreviewed
                              </small>
                            </TableCell>
                            <TableCell>{methods[s.result.method]}</TableCell>
                            <TableCell className="numeric">
                              {fmt(s.result.rate)}
                            </TableCell>
                            <TableCell>
                              <span className="tag">{s.draft.provenance}</span>
                            </TableCell>
                            <TableCell>
                              <div className="inline">
                                <Button
                                  variant="ghost"
                                  onClick={() => {
                                    revision.current++;
                                    setDraft({ ...s.draft });
                                    setActive(s);
                                    setPreview(s.result);
                                    setView('assessment');
                                    setError('');
                                    setMessage(
                                      'Saved assessment opened; editing creates a new calculation.',
                                    );
                                  }}
                                >
                                  Open <ArrowUpRight />
                                </Button>
                                <Button
                                  variant="ghost"
                                  aria-label={`Delete ${s.draft.name}`}
                                  onClick={() => setConfirm(s.id)}
                                >
                                  <Trash2 size={16} />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  <p className="comparison-note">
                    Compare equivalent locations, methods, exposure windows and
                    conditions. A lower rate does not by itself establish a
                    safer material or asset.
                  </p>
                </>
              )}
            </>
          )}
          {view === 'evidence' && <Evidence />}
          {view === 'galvanic' && <GalvanicResearch />}
        </div>
        <footer className="workspace-footer">
          <span>MAST CORROSION</span>
          <span>Uniform-loss research preview · Engineer review required</span>
        </footer>
      </main>
      <AlertDialog
        open={!!confirm}
        onOpenChange={(open) => {
          if (!open) setConfirm(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirm === 'new'
                ? 'Start a new assessment?'
                : 'Remove saved assessment?'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirm === 'new'
                ? 'This clears the current inputs. Saved assessments are retained; export or save any work you need first.'
                : 'This removes only this browser’s copy. Export a report first if you need a backup.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (confirm === 'new') reset();
                else if (confirm) {
                  if (persist(saved.filter((s) => s.id !== confirm)))
                    setMessage('Saved assessment removed from this device.');
                }
                setConfirm(null);
              }}
            >
              {confirm === 'new' ? 'Start new' : 'Remove'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </SidebarProvider>
  );
}
