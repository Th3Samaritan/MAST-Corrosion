/** MAST uniform-corrosion engine. Units are part of every input contract.
 * No legacy synthetic labels or neural network outputs are used here.
 */
export const ENGINE_VERSION = '0.1.0';
export const YEAR_DAYS = 365;
export const FARADAY_FACTOR = 0.003272;
export const methods = {
  thickness: 'Thickness history',
  current: 'Corrosion current',
  lpr: 'Polarization resistance',
  coupon: 'Coupon mass loss',
} as const;
export type Method = keyof typeof methods;
export type Draft = {
  method: Method;
  name: string;
  material: string;
  environment: string;
  source: string;
  provenance: string;
  mechanism: string;
  notes: string;
  readings: string;
  density: string;
  equivalentWeight: string;
  current: string;
  resistance: string;
  betaA: string;
  betaC: string;
  loss: string;
  cleaning: string;
  area: string;
  hours: string;
  latest: string;
  minimum: string;
  horizon: string;
  tolerance: string;
  sensitivity: string;
};
export const example: Draft = {
  method: 'thickness',
  name: 'Cooling water line / CML-04',
  material: 'Carbon steel',
  environment:
    'Illustrative cooling-water service; unchanged conditions assumed',
  source: 'Illustrative fixture — not field measurements',
  provenance: 'example',
  mechanism: 'uniform',
  notes: '',
  readings:
    'date,thickness_mm\n2023-01-01,8.00\n2024-01-01,7.81\n2025-01-01,7.59\n2026-01-01,7.40',
  density: '7.87',
  equivalentWeight: '27.9225',
  current: '10',
  resistance: '1000',
  betaA: '120',
  betaC: '120',
  loss: '100',
  cleaning: '0',
  area: '10',
  hours: '168',
  latest: '7.4',
  minimum: '5',
  horizon: '10',
  tolerance: '0.05',
  sensitivity: '20',
};
export type Reading = { date: string; thickness: number; years: number };
export type Result = {
  version: string;
  method: Method;
  rate: number;
  range: [number, number];
  rangeLabel: string;
  current: number | null;
  latest: number;
  minimum: number;
  horizon: number;
  yearsToMinimum: number | null;
  thresholdState: 'reached' | 'conditional' | 'unresolved';
  readings: Reading[];
  warnings: string[];
  formula: string;
  basis: string;
  trace: { label: string; value: string }[];
};
export class InputError extends Error {
  field: string;
  constructor(field: string, message: string) {
    super(message);
    this.name = 'InputError';
    this.field = field;
  }
}
export function numeric(
  value: unknown,
  field: string,
  min = 0,
  inclusive = false,
  max = 1e9,
): number {
  if (
    typeof value !== 'string' ||
    !value.trim() ||
    !/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(value.trim())
  )
    throw new InputError(field, `${field}: enter a numeric value.`);
  const n = Number(value);
  if (!Number.isFinite(n) || (inclusive ? n < min : n <= min) || n > max)
    throw new InputError(
      field,
      `${field}: must be ${inclusive ? 'at least' : 'greater than'} ${min} and no more than ${max}.`,
    );
  return n;
}
export function validateDraft(value: unknown): Draft {
  if (!value || typeof value !== 'object' || Array.isArray(value))
    throw new InputError('assessment', 'Expected an assessment object.');
  const obj = value as Record<string, unknown>;
  for (const key of Object.keys(example))
    if (typeof obj[key] !== 'string' || (obj[key] as string).length > 200000)
      throw new InputError(key, `Missing or invalid ${key}.`);
  if ((obj.name as string).length > 1000)
    throw new InputError(
      'name',
      'Assessment name must be at most 1,000 characters.',
    );
  if (!Object.hasOwn(methods, obj.method as string))
    throw new InputError('method', 'Choose a supported calculation method.');
  if (!['example', 'measurement', 'assumed'].includes(obj.provenance as string))
    throw new InputError(
      'provenance',
      'Choose example, measurement or assumed provenance.',
    );
  if (
    !['uniform', 'pitting', 'galvanic', 'cracking', 'unknown'].includes(
      obj.mechanism as string,
    )
  )
    throw new InputError('mechanism', 'Choose a recognized mechanism.');
  return Object.fromEntries(
    Object.keys(example).map((k) => [k, obj[k]]),
  ) as Draft;
}
export function parseReadings(csv: string): Reading[] {
  if (csv.length > 200000)
    throw new InputError('readings', 'CSV exceeds 200 KB.');
  const lines = csv
    .replace(/^\uFEFF/, '')
    .trim()
    .split(/\r?\n/)
    .filter((x) => x.trim());
  if (lines[0]?.trim() !== 'date,thickness_mm')
    throw new InputError(
      'readings',
      'CSV header must be date,thickness_mm. Use one inspection location per assessment.',
    );
  if (lines.length < 3 || lines.length > 1001)
    throw new InputError('readings', 'Provide 2–1,000 dated measurements.');
  const seen = new Set<string>();
  const readings = lines
    .slice(1)
    .map((line, index) => {
      const cells = line.split(',').map((x) => x.trim());
      const date = cells[0];
      if (cells.length !== 2 || !/^\d{4}-\d{2}-\d{2}$/.test(date))
        throw new InputError(
          'readings',
          `Row ${index + 2}: expected YYYY-MM-DD,thickness_mm.`,
        );
      const ms = Date.parse(date + 'T00:00:00Z');
      if (
        !Number.isFinite(ms) ||
        new Date(ms).toISOString().slice(0, 10) !== date ||
        date < '1900-01-01' ||
        date > '2100-12-31'
      )
        throw new InputError(
          'readings',
          `Row ${index + 2}: invalid date (1900–2100 supported).`,
        );
      if (seen.has(date))
        throw new InputError(
          'readings',
          `Duplicate date ${date}. Resolve repeat readings before import.`,
        );
      seen.add(date);
      return {
        date,
        thickness: numeric(
          cells[1],
          `Row ${index + 2} thickness`,
          0,
          false,
          10000,
        ),
        years: ms / (86400000 * YEAR_DAYS),
      };
    })
    .sort((a, b) => a.years - b.years);
  const start = readings[0].years;
  return readings.map((r) => ({ ...r, years: r.years - start }));
}
export const faraday = (current: number, ew: number, density: number) =>
  (FARADAY_FACTOR * current * ew) / density;

export function calculate(value: unknown): Result {
  const d = validateDraft(value);
  for (const field of ['name', 'material', 'environment', 'source'] as const)
    if (!d[field].trim())
      throw new InputError(field, `Record the ${field} before calculating.`);
  if (d.mechanism !== 'uniform')
    throw new InputError(
      'mechanism',
      'This engine supports uniform metal loss only. Identify the mechanism and obtain a specialist assessment for localized attack, galvanic prediction or cracking.',
    );
  const minimum = numeric(d.minimum, 'Minimum thickness', 0, false, 10000);
  const horizon = numeric(d.horizon, 'Forecast horizon', 0, false, 100);
  let latest = 0,
    rate = 0,
    current: number | null = null,
    readings: Reading[] = [],
    formula = '',
    basis = '',
    range: [number, number] = [0, 0],
    rangeLabel = '';
  const trace: Result['trace'] = [];
  const warnings = [
    'Future thickness assumes constant rate and unchanged exposure. This is not an inspection interval or fitness-for-service assessment.',
  ];
  if (d.provenance === 'example')
    warnings.push(
      'Illustrative inputs: no field accuracy or real asset condition is established.',
    );
  if (d.provenance === 'assumed')
    warnings.push(
      'Assumed inputs: this is a scenario, not a measurement-backed result.',
    );
  if (d.method === 'thickness') {
    readings = parseReadings(d.readings);
    latest = readings.at(-1)!.thickness;
    const tol = numeric(d.tolerance, 'Thickness tolerance', 0, true, 10);
    const meanX = readings.reduce((s, r) => s + r.years, 0) / readings.length;
    const meanY =
      readings.reduce((s, r) => s + r.thickness, 0) / readings.length;
    const denominator = readings.reduce(
      (s, r) => s + (r.years - meanX) ** 2,
      0,
    );
    const slope =
      readings.reduce(
        (s, r) => s + (r.years - meanX) * (r.thickness - meanY),
        0,
      ) / denominator;
    rate = -slope;
    const bound =
      tol *
      readings.reduce((s, r) => s + Math.abs(r.years - meanX) / denominator, 0);
    range = [Math.max(0, rate - bound), Math.max(0, rate + bound)];
    rangeLabel = 'Input-tolerance bounds';
    const residual = Math.max(
      ...readings.map((r) =>
        Math.abs(r.thickness - (meanY + slope * (r.years - meanX))),
      ),
    );
    if (residual > Math.max(tol, 1e-10))
      warnings.push(
        'Deviation from the fitted trend exceeds the entered tolerance. Check measurement consistency and changing corrosion conditions.',
      );
    if (rate <= bound)
      warnings.push(
        'Positive loss is not resolved within the entered tolerance. A reliable time-to-minimum cannot be established.',
      );
    if (
      readings.some(
        (r, i) => i > 0 && r.thickness > readings[i - 1].thickness + 2 * tol,
      )
    )
      warnings.push(
        'Thickness increased beyond the stated tolerance between readings. Check location, calibration, coatings and repairs.',
      );
    if (horizon > readings.at(-1)!.years)
      warnings.push(
        'The forecast extends beyond the observation duration; long-range extrapolation is unvalidated.',
      );
    formula =
      'rate = −Σ[(t − mean(t)) × (thickness − mean(thickness))] / Σ(t − mean(t))²';
    basis = 'Least-squares trend at one inspection location';
    trace.push(
      {
        label: 'Observation span',
        value: `${readings.at(-1)!.years.toFixed(4)} years (365 days/year)`,
      },
      {
        label: 'Readings / absolute tolerance',
        value: `${readings.length} / ±${tol} mm per reading`,
      },
      {
        label: 'Latest observation',
        value: `${readings.at(-1)!.date}: ${latest} mm`,
      },
      {
        label: 'Signed fitted loss rate',
        value: `${rate.toPrecision(7)} mm/year`,
      },
    );
  } else {
    latest = numeric(d.latest, 'Latest thickness', 0, false, 10000);
    const density = numeric(d.density, 'Density', 0, false, 30);
    if (d.method === 'coupon') {
      const loss = numeric(d.loss, 'Gross mass loss', 0, true);
      const cleaning = numeric(d.cleaning, 'Cleaning correction', 0, true);
      if (cleaning > loss)
        throw new InputError(
          'cleaning',
          'Cleaning correction exceeds gross loss. Resolve the measurement; negative metal loss is not a corrosion rate.',
        );
      const area = numeric(d.area, 'Exposed area');
      const hours = numeric(d.hours, 'Exposure hours');
      rate = (87.6 * (loss - cleaning)) / (density * area * hours);
      formula =
        'rate [mm/year] = 87.6 × corrected loss [mg] / (ρ [g/cm³] × A [cm²] × exposure [h])';
      basis = 'Exposure-average uniform coupon loss';
      warnings.push(
        'Coupon-to-asset transfer requires representative alloy, exposure and surface condition. Cleaning correction must be independently established.',
      );
      trace.push(
        { label: 'Corrected mass loss', value: `${loss - cleaning} mg` },
        { label: 'Area / exposure', value: `${area} cm² / ${hours} h` },
      );
    } else {
      const ew = numeric(
        d.equivalentWeight,
        'Equivalent weight',
        0,
        false,
        300,
      );
      current =
        d.method === 'current'
          ? numeric(d.current, 'Corrosion current density', 0, true, 1e7)
          : 0;
      if (d.method === 'lpr') {
        const a = numeric(d.betaA, 'Anodic Tafel slope', 0, false, 1000),
          b = numeric(d.betaC, 'Cathodic Tafel slope', 0, false, 1000);
        const rp = numeric(
          d.resistance,
          'Polarization resistance',
          0,
          false,
          1e12,
        );
        const B = (a * b) / (2.303 * (a + b));
        current = (1000 * B) / rp;
        trace.push(
          { label: 'Stern–Geary coefficient', value: `${B.toPrecision(7)} mV` },
          { label: 'Area-normalized Rp', value: `${rp} Ω·cm²` },
        );
        warnings.push(
          'LPR assumes suitable near-open-circuit behavior, independent Tafel slopes and solution-resistance correction. Passivation and transport limitation can invalidate it.',
        );
      }
      rate = faraday(current, ew, density);
      formula =
        (d.method === 'lpr'
          ? 'B = βaβc / [2.303(βa + βc)]; i = 1000B / Rp; '
          : '') +
        'rate [mm/year] = 0.003272 × i [µA/cm²] × EW [g/equiv] / ρ [g/cm³]';
      basis =
        d.method === 'lpr'
          ? 'Stern–Geary estimate + Faraday conversion'
          : 'Faraday conversion of supplied corrosion current density';
      trace.push(
        {
          label: 'Corrosion current density',
          value: `${current.toPrecision(7)} µA/cm²`,
        },
        { label: 'Equivalent weight', value: `${ew} g/equivalent` },
      );
      warnings.push(
        'Equivalent weight and dissolution valence must match the material. Use corrosion/dissolution current, not net current measured at open circuit.',
      );
    }
    const sensitivity =
      numeric(d.sensitivity, 'Sensitivity range', 0, true, 100) / 100;
    range = [rate * (1 - sensitivity), rate * (1 + sensitivity)];
    rangeLabel = 'User-defined rate sensitivity';
    trace.push(
      { label: 'Density', value: `${density} g/cm³` },
      {
        label: 'Sensitivity assumption',
        value: `±${sensitivity * 100}% on calculated rate; not a confidence interval`,
      },
    );
    warnings.push(
      'The sensitivity range is user-selected, not calibrated predictive uncertainty.',
    );
  }
  if (!Number.isFinite(rate) || !range.every(Number.isFinite))
    throw new InputError(
      'inputs',
      'Inputs exceed the numerical range of this engine.',
    );
  const resolved = rate > 0 && range[0] > 0;
  const thresholdState =
    latest <= minimum ? 'reached' : resolved ? 'conditional' : 'unresolved';
  const yearsToMinimum =
    latest <= minimum ? 0 : resolved ? (latest - minimum) / rate : null;
  if (latest <= minimum)
    warnings.unshift(
      'Latest thickness is at or below your supplied minimum. Refer for engineering review; no remaining margin is shown.',
    );
  if (rate <= 0)
    warnings.push(
      'No positive loss trend is established. This does not demonstrate that the asset is safe or that future corrosion is zero.',
    );
  return {
    version: ENGINE_VERSION,
    method: d.method,
    rate,
    range,
    rangeLabel,
    current,
    latest,
    minimum,
    horizon,
    yearsToMinimum,
    thresholdState,
    readings,
    warnings,
    formula,
    basis,
    trace,
  };
}

export function projectedThickness(
  r: Result,
  years: number,
  rate = r.rate,
): number {
  return Math.max(0, r.latest - Math.max(0, rate) * years);
}
