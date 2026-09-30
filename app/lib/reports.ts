import { calculate, validateDraft, ENGINE_VERSION } from './corrosion';
import type { Draft, Result } from './corrosion';
export type Snapshot = {
  id: string;
  createdAt: string;
  draft: Draft;
  result: Result;
  status: 'unreviewed';
  schema: 1;
};
export function snapshot(draft: Draft): Snapshot {
  return {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    draft: validateDraft(draft),
    result: calculate(draft),
    status: 'unreviewed',
    schema: 1,
  };
}
/** Never trust cached or imported result numbers; recompute using the current engine. */
export function restoreSnapshots(value: unknown): Snapshot[] {
  if (!Array.isArray(value) || value.length > 100)
    throw new Error('Expected at most 100 saved assessments.');
  const ids = new Set<string>();
  return value.map((item) => {
    if (
      !item ||
      item.schema !== 1 ||
      typeof item.id !== 'string' ||
      ids.has(item.id) ||
      typeof item.createdAt !== 'string' ||
      !Number.isFinite(Date.parse(item.createdAt))
    )
      throw new Error('Saved assessment format is invalid.');
    ids.add(item.id);
    const draft = validateDraft(item.draft);
    return {
      id: item.id,
      createdAt: item.createdAt,
      draft,
      result: calculate(draft),
      status: 'unreviewed',
      schema: 1,
    };
  });
}
export function markdownReport(s: Snapshot): string {
  const r = s.result;
  const text = (v: string) => v.replace(/[\r\n]+/g, ' ').replace(/[|]/g, '/');
  return `# MAST Corrosion assessment\n\n${text(s.draft.name)}\n\nStatus: unreviewed engineering draft. Provenance: ${s.draft.provenance}.\nCreated: ${s.createdAt}. Engine: ${ENGINE_VERSION}.\n\n## Result\n\nSigned uniform loss rate: ${r.rate.toPrecision(6)} mm/year.\n${r.rangeLabel}: ${r.range.map((x) => x.toPrecision(6)).join(' to ')} mm/year.\nLatest thickness: ${r.latest} mm. Supplied minimum: ${r.minimum} mm.\nConditional time to minimum: ${r.yearsToMinimum === null ? 'unresolved' : r.yearsToMinimum.toPrecision(5) + ' years'}. This is not safe service life or an inspection interval.\n\n## Basis\n\n${r.basis}\n\n${r.formula}\n\n${r.trace.map((t) => '- ' + t.label + ': ' + t.value).join('\n')}\n\n## Evidence\n\nMaterial: ${text(s.draft.material)}\n\nEnvironment: ${text(s.draft.environment)}\n\nSource: ${text(s.draft.source)}\n\nNotes: ${text(s.draft.notes) || 'None recorded'}\n\n## Limitations\n\n${r.warnings.map((w) => '- ' + w).join('\n')}\n\n## Reproducible inputs\n\n\`\`\`json\n${JSON.stringify(s.draft, null, 2)}\n\`\`\`\n\n## References\n\n- [ASTM G102 scope](https://store.astm.org/standards/g102)\n- [Gamry corrosion calculation basis](https://help.gamry.com/Framework/experiments_c-dccorrosion.html)\n- [ASTM G31 scope](https://store.astm.org/standards/g31)\n\nNo standards conformance or field validation is asserted.\n`;
}
