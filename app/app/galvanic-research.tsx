'use client';
import { useEffect, useRef, useState } from 'react';
import { apiRequest, getSupabase } from '@/lib/cloud';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableCell,
  TableRow,
} from '@/components/ui/table';
type Material = {
  Material: string;
  Group: string;
  Rank: string;
  Potential_V_SCE: string;
};
type Prediction = {
  anode: string;
  cathode: string;
  environment: string;
  area_ratio: number;
  current_proxy: number;
  unfavorable_score: number;
  classification: string;
  v_anode: number;
  v_cathode: number;
};
type Training = {
  run: string;
  epochs: number;
  history: Record<string, number>[];
};
function Choice({
  label,
  value,
  values,
  onChange,
}: {
  label: string;
  value: string;
  values: string[];
  onChange: (value: string) => void;
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
          <SelectValue>{value || 'Select…'}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {values.map((v) => (
            <SelectItem value={v} key={v}>
              {v}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
function csvDownload(rows: Prediction[]) {
  const fields: (keyof Prediction)[] = [
    'anode',
    'cathode',
    'environment',
    'area_ratio',
    'current_proxy',
    'unfavorable_score',
    'classification',
    'v_anode',
    'v_cathode',
  ];
  const cell = (v: unknown) => '"' + String(v).replace(/"/g, '""') + '"';
  const text = [
    fields.join(','),
    ...rows.map((r) => fields.map((f) => cell(r[f])).join(',')),
  ].join('\n');
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv' }));
  const a = document.createElement('a');
  a.href = url;
  a.download = 'mast-research-predictions.csv';
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function GalvanicResearch() {
  const [materials, setMaterials] = useState<Material[]>([]),
    [envs, setEnvs] = useState<string[]>([]),
    [anode, setAnode] = useState(''),
    [cathode, setCathode] = useState(''),
    [env, setEnv] = useState(''),
    [ratio, setRatio] = useState('1'),
    [run, setRun] = useState('1');
  const [results, setResults] = useState<Prediction[]>([]),
    [resultRun, setResultRun] = useState(''),
    [runs, setRuns] = useState<Training[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [csv, setCsv] = useState('anode,cathode,environment,area_ratio\n');
  const [heatmap, setHeatmap] = useState<{
    names: string[];
    values: Prediction[];
  } | null>(null);
  const request = useRef(0);
  useEffect(() => {
    const invalidate = () => {
      request.current++;
    };
    const client = getSupabase();
    const subscription = client?.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_OUT') {
        request.current++;
        setResults([]);
        setRuns([]);
        setMaterials([]);
        setHeatmap(null);
        setBusy(false);
      }
    });
    return () => {
      invalidate();
      subscription?.data.subscription.unsubscribe();
    };
  }, []);
  async function action(task: () => Promise<void>) {
    setError('');
    setBusy(true);
    try {
      await task();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function load() {
    const epoch = ++request.current;
    await action(async () => {
      const catalog = await apiRequest<{
        materials: Material[];
        environments: string[];
      }>('/v1/model/catalog', {}, true);
      if (epoch !== request.current) return;
      setMaterials(catalog.materials);
      setEnvs(catalog.environments);
      setAnode(catalog.materials.at(-1)?.Material || '');
      setCathode(catalog.materials[0]?.Material || '');
      setEnv(catalog.environments[0] || '');
    });
  }
  async function predict(mode: 'single' | 'csv' | 'heatmap') {
    const epoch = ++request.current;
    const usedRun = run;
    await action(async () => {
      let pairs: object[] | undefined;
      let names: string[] = [];
      if (mode !== 'csv') {
        const n = Number(ratio);
        if (!ratio.trim() || !Number.isFinite(n) || n < 0.01 || n > 50)
          throw new Error('Area ratio must be 0.01–50.');
        if (mode === 'single')
          pairs = [{ anode, cathode, environment: env, area_ratio: n }];
        else {
          const groups = new Map<string, Material>();
          for (const m of materials)
            if (!groups.has(m.Group)) groups.set(m.Group, m);
          names = [...groups.values()].map((m) => m.Material);
          pairs = names.flatMap((a) =>
            names.map((c) => ({
              anode: a,
              cathode: c,
              environment: env,
              area_ratio: n,
            })),
          );
        }
      }
      const data = await apiRequest<{ results: Prediction[] }>(
        '/v1/model/predict',
        {
          method: 'POST',
          body: JSON.stringify({
            run: usedRun,
            pairs,
            ...(mode === 'csv' ? { csv } : {}),
          }),
        },
        true,
      );
      if (epoch !== request.current) return;
      setResultRun(usedRun);
      setResults(data.results);
      setHeatmap(mode === 'heatmap' ? { names, values: data.results } : null);
    });
  }
  async function training() {
    const epoch = ++request.current;
    await action(async () => {
      const data = await apiRequest<{ runs: Training[] }>(
        '/v1/model/training',
        {},
        true,
      );
      if (epoch === request.current) setRuns(data.runs);
    });
  }
  return (
    <div className="research-workspace">
      <div className="notice">
        Synthetic-trained galvanic research model. Current proxy and
        classification scores are not validated corrosion rates or calibrated
        probabilities. Do not convert this output to mm/year.
      </div>
      <div className="panel">
        <div className="cloud-actions">
          <h2>Existing PINN checkpoints</h2>
          <Button variant="outline" disabled={busy} onClick={() => void load()}>
            Load material reference
          </Button>
          <Button
            variant="outline"
            disabled={busy}
            onClick={() => void training()}
          >
            Load training history
          </Button>
        </div>
        <p>
          Sign in under Saved comparisons to access the model on Render. The
          original three checkpoints are retained; model loading happens on
          demand.
        </p>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {busy && (
          <p role="status">
            Loading model data… The first prediction may take longer.
          </p>
        )}
      </div>
      <Tabs defaultValue="predict">
        <TabsList>
          <TabsTrigger value="predict">Predictions</TabsTrigger>
          <TabsTrigger value="materials">Galvanic series</TabsTrigger>
          <TabsTrigger value="training">Training analytics</TabsTrigger>
        </TabsList>
        <TabsContent value="predict">
          <div className="assessment-grid">
            <section className="panel">
              <h2>Research inputs</h2>
              <Choice
                label="Checkpoint run"
                value={run}
                values={['1', '2', '3']}
                onChange={setRun}
              />
              <Choice
                label="Anode input"
                value={anode}
                values={materials.map((m) => m.Material)}
                onChange={setAnode}
              />
              <Choice
                label="Cathode input"
                value={cathode}
                values={materials.map((m) => m.Material)}
                onChange={setCathode}
              />
              <Choice
                label="Environment"
                value={env}
                values={envs}
                onChange={setEnv}
              />
              <label className="field">
                Cathode / anode area ratio
                <input
                  type="number"
                  step="any"
                  min="0.01"
                  max="50"
                  value={ratio}
                  onChange={(e) => setRatio(e.target.value)}
                />
              </label>
              <p className="field-note">
                Input order is preserved to reproduce the original model. Verify
                the actual anodic/cathodic behavior for your environment.
              </p>
              <div className="output-actions">
                <Button
                  className="primary"
                  disabled={busy || !anode || !cathode}
                  onClick={() => void predict('single')}
                >
                  Predict pair
                </Button>
                <Button
                  variant="outline"
                  disabled={busy || !materials.length}
                  onClick={() => void predict('heatmap')}
                >
                  Group heatmap
                </Button>
              </div>
              <details className="evidence-details">
                <summary>Batch CSV predictions</summary>
                <label className="field">
                  CSV pairs
                  <textarea
                    value={csv}
                    onChange={(e) => setCsv(e.target.value)}
                  />
                  <small>
                    Up to 400 rows. Quote material names that contain commas.
                    Columns: anode,cathode,environment,area_ratio.
                  </small>
                </label>
                <label className="field">
                  Load CSV file
                  <input
                    type="file"
                    accept=".csv"
                    disabled={busy}
                    onChange={async (e) => {
                      const f = e.target.files?.[0];
                      if (!f) return;
                      if (f.size > 200000) {
                        setError('CSV exceeds 200 KB.');
                        return;
                      }
                      try {
                        setCsv(await f.text());
                      } catch {
                        setError('Could not read CSV.');
                      }
                      e.target.value = '';
                    }}
                  />
                </label>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => void predict('csv')}
                >
                  Run batch
                </Button>
              </details>
            </section>
            <section className="panel">
              <h2>Research results {resultRun && `· Run ${resultRun}`}</h2>
              {!results.length ? (
                <p>
                  No prediction yet. Load the reference, choose a pair and run
                  the model.
                </p>
              ) : (
                <>
                  <p>
                    Results belong to the last completed request. Changing
                    controls does not recalculate them.
                  </p>
                  <Button
                    variant="outline"
                    onClick={() => csvDownload(results)}
                  >
                    Export results CSV
                  </Button>
                  {heatmap && (
                    <div className="heatmap">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Anode ↓ / Cathode →</TableHead>
                            {heatmap.names.map((name, i) => (
                              <TableHead key={name} title={name}>
                                {i + 1}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {heatmap.names.map((name, i) => (
                            <TableRow key={name}>
                              <TableCell>
                                {i + 1}. {name}
                              </TableCell>
                              {heatmap.names.map((c, j) => {
                                const value =
                                  heatmap.values[i * heatmap.names.length + j];
                                return (
                                  <TableCell
                                    key={c}
                                    style={{
                                      background: `rgba(200,70,32,${value.unfavorable_score * 0.4})`,
                                    }}
                                    title={`${name} → ${c}: ${value.unfavorable_score.toFixed(3)}`}
                                  >
                                    {value.unfavorable_score.toFixed(2)}
                                  </TableCell>
                                );
                              })}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <p>
                        Heatmap: unfavorable classification score; one reference
                        material per group. Diagonal values reproduce the model,
                        not proof of self-corrosion rate.
                      </p>
                    </div>
                  )}
                  <div className="prediction-table">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Pair / exposure</TableHead>
                          <TableHead>Current proxy</TableHead>
                          <TableHead>Unfavorable score</TableHead>
                          <TableHead>Class</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {results.map((r, i) => (
                          <TableRow key={i}>
                            <TableCell>
                              {r.anode} → {r.cathode}
                              <small className="table-date">
                                {r.environment} · area ratio {r.area_ratio}
                              </small>
                            </TableCell>
                            <TableCell>
                              {r.current_proxy.toPrecision(5)}
                            </TableCell>
                            <TableCell>
                              {r.unfavorable_score.toFixed(3)}
                            </TableCell>
                            <TableCell>{r.classification}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </>
              )}
            </section>
          </div>
        </TabsContent>
        <TabsContent value="materials">
          <section className="panel">
            <h2>Repository galvanic reference</h2>
            <p>
              These are the supplied model features, not newly verified standard
              tables. Potentials are recorded versus SCE; environment and
              surface condition govern their applicability.
            </p>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rank</TableHead>
                  <TableHead>Material</TableHead>
                  <TableHead>Potential · V vs SCE</TableHead>
                  <TableHead>Group</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {materials.map((m) => (
                  <TableRow key={m.Material}>
                    <TableCell>{m.Rank}</TableCell>
                    <TableCell>{m.Material}</TableCell>
                    <TableCell>{m.Potential_V_SCE}</TableCell>
                    <TableCell>{m.Group}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </section>
        </TabsContent>
        <TabsContent value="training">
          <div className="method-grid">
            {!runs.length && (
              <p className="panel">
                Load training history to inspect the three stored runs.
              </p>
            )}
            {runs.map((r) => {
              const last = r.history.at(-1)!;
              const max = Math.max(...r.history.map((x) => x.val_total), 1e-9);
              return (
                <section className="panel" key={r.run}>
                  <h2>
                    Run {r.run} · {r.epochs} epochs
                  </h2>
                  <p>
                    Final logged validation loss:{' '}
                    {last.val_total.toPrecision(4)}. This is the last epoch, not
                    necessarily the best checkpoint.
                  </p>
                  <svg
                    viewBox="0 0 400 150"
                    role="img"
                    aria-label={`Validation loss history for run ${r.run}; exact values follow in the table.`}
                  >
                    <polyline
                      fill="none"
                      stroke="#008599"
                      strokeWidth="2"
                      points={r.history
                        .map(
                          (row, i) =>
                            `${10 + (380 * i) / Math.max(1, r.history.length - 1)},${135 - (120 * row.val_total) / max}`,
                        )
                        .join(' ')}
                    />
                    <text x="10" y="148" fontSize="12">
                      Epoch 1
                    </text>
                    <text x="320" y="148" fontSize="12">
                      Epoch {r.epochs}
                    </text>
                  </svg>
                  <details>
                    <summary>View logged metrics</summary>
                    <div className="prediction-table">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Epoch</TableHead>
                            <TableHead>Val loss</TableHead>
                            <TableHead>MAE</TableHead>
                            <TableHead>Accuracy</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {r.history.map((row) => (
                            <TableRow key={row.epoch}>
                              <TableCell>{row.epoch}</TableCell>
                              <TableCell>
                                {row.val_total.toPrecision(4)}
                              </TableCell>
                              <TableCell>
                                {row.val_mae.toPrecision(4)}
                              </TableCell>
                              <TableCell>
                                {row.val_accuracy.toFixed(3)}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </details>
                  <p className="field-note">
                    Synthetic validation metrics do not establish real-world
                    corrosion accuracy.
                  </p>
                </section>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
