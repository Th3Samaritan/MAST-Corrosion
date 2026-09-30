import { createClient } from '@supabase/supabase-js';
import type { SupabaseClient } from '@supabase/supabase-js';
import { snapshot } from './reports';
import type { Draft, Result } from './corrosion';

export const apiUrl = (process.env.NEXT_PUBLIC_API_URL || '').replace(
  /\/$/,
  '',
);
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || '';
export const cloudConfigured = Boolean(
  apiUrl &&
  supabaseUrl &&
  publishableKey &&
  !supabaseUrl.includes('YOUR_PROJECT'),
);
let client: SupabaseClient | null = null;
export function getSupabase() {
  if (!cloudConfigured) return null;
  if (!client) client = createClient(supabaseUrl, publishableKey);
  return client;
}
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  authenticated = false,
): Promise<T> {
  if (!apiUrl) throw new Error('The Render API URL has not been configured.');
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (authenticated) {
    const supabase = getSupabase();
    if (!supabase) throw new Error('Cloud storage has not been configured.');
    const { data, error } = await supabase.auth.getSession();
    if (error || !data.session)
      throw new Error('Sign in to access cloud assessments.');
    headers.set('Authorization', `Bearer ${data.session.access_token}`);
  }
  let response: Response;
  try {
    response = await fetch(apiUrl + path, {
      ...options,
      headers,
      signal: AbortSignal.timeout(60000),
    });
  } catch {
    throw new Error(
      'The API could not be reached. Your inputs are retained. Render may be starting; try again shortly.',
    );
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new Error('The API returned an invalid response.');
  }
  if (!response.ok)
    throw new Error(
      typeof body === 'object' && body && 'error' in body
        ? String(body.error)
        : 'The request failed.',
    );
  return body as T;
}
export async function calculateAssessment(draft: Draft) {
  const s = snapshot(draft);
  if (apiUrl) {
    const { result } = await apiRequest<{ result: Result }>('/v1/calculate', {
      method: 'POST',
      body: JSON.stringify({ draft: s.draft }),
    });
    if (result.version !== s.result.version)
      throw new Error(
        'Frontend and API engine versions differ. Deploy matching releases.',
      );
    s.result = result;
  }
  return s;
}
