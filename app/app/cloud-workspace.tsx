'use client';
import { useEffect, useRef, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import type { Draft } from '@/lib/corrosion';
import type { Snapshot } from '@/lib/reports';
import { restoreSnapshots } from '@/lib/reports';
import { apiRequest, cloudConfigured, getSupabase } from '@/lib/cloud';
import { Button } from '@/components/ui/button';
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
type Row = {
  id: string;
  created_at: string;
  name: string;
  method: string;
  engine_version: string;
};
type Stored = Row & { draft: Draft };

export function CloudWorkspace({
  draft,
  onLoad,
}: {
  draft: Draft;
  onLoad: (s: Snapshot) => void;
}) {
  const [session, setSession] = useState<Session | null>(null),
    [ready, setReady] = useState(false),
    [email, setEmail] = useState(''),
    [password, setPassword] = useState('');
  const [rows, setRows] = useState<Row[]>([]),
    [next, setNext] = useState<string | null>(null),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState(''),
    [error, setError] = useState(''),
    [remove, setRemove] = useState<string | null>(null);
  const generation = useRef(0);
  const pendingSave = useRef<{ draft: string; id: string } | null>(null);
  useEffect(() => {
    const client = getSupabase();
    if (!client) {
      setReady(true);
      return;
    }
    let alive = true;
    const invalidate = () => {
      generation.current++;
    };
    void client.auth.getSession().then(({ data, error }) => {
      if (alive) {
        if (error) setError('Could not restore your session. Please sign in.');
        setSession(data.session);
        setReady(true);
      }
    });
    const { data } = client.auth.onAuthStateChange((_event, value) => {
      if (alive) {
        setSession(value);
        setReady(true);
      }
    });
    return () => {
      alive = false;
      data.subscription.unsubscribe();
      invalidate();
    };
  }, []);
  const userId = session?.user.id;
  useEffect(() => {
    generation.current++;
    setRows([]);
    setNext(null);
    setNotice('');
    setError('');
    pendingSave.current = null;
    if (userId) void load();
  }, [userId]); // user changes invalidate in-flight results
  async function load(cursor?: string) {
    const epoch = generation.current;
    setBusy(true);
    setError('');
    try {
      const result = await apiRequest<{
        assessments: Row[];
        nextCursor: string | null;
      }>(
        '/v1/assessments' +
          (cursor ? '?before=' + encodeURIComponent(cursor) : ''),
        {},
        true,
      );
      if (epoch === generation.current) {
        setRows((old) =>
          cursor ? [...old, ...result.assessments] : result.assessments,
        );
        setNext(result.nextCursor);
      }
    } catch (e) {
      if (epoch === generation.current) setError((e as Error).message);
    } finally {
      if (epoch === generation.current) setBusy(false);
    }
  }
  async function authenticate(signUp = false) {
    const client = getSupabase();
    if (!client) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = signUp
        ? await client.auth.signUp({ email, password })
        : await client.auth.signInWithPassword({ email, password });
      if (result.error) throw result.error;
      setPassword('');
      if (signUp && !result.data.session)
        setNotice(
          'Check your email to confirm your account, then return here to sign in.',
        );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function saveCloud() {
    const epoch = generation.current;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const key = JSON.stringify(draft);
      if (pendingSave.current?.draft !== key)
        pendingSave.current = { draft: key, id: crypto.randomUUID() };
      await apiRequest(
        '/v1/assessments',
        {
          method: 'POST',
          body: JSON.stringify({ id: pendingSave.current.id, draft }),
        },
        true,
      );
      if (epoch === generation.current) {
        setNotice('Snapshot saved to your private cloud workspace.');
        await load();
      }
    } catch (e) {
      if (epoch === generation.current) setError((e as Error).message);
    } finally {
      if (epoch === generation.current) setBusy(false);
    }
  }
  async function open(id: string) {
    const epoch = generation.current;
    setBusy(true);
    setError('');
    try {
      const { assessment } = await apiRequest<{ assessment: Stored }>(
        '/v1/assessments/' + id,
        {},
        true,
      );
      const [s] = restoreSnapshots([
        {
          schema: 1,
          id: assessment.id,
          createdAt: assessment.created_at,
          draft: assessment.draft,
        },
      ]);
      if (epoch === generation.current) onLoad(s);
    } catch (e) {
      if (epoch === generation.current) setError((e as Error).message);
    } finally {
      if (epoch === generation.current) setBusy(false);
    }
  }
  async function deleteRow(id: string) {
    const epoch = generation.current;
    setBusy(true);
    setError('');
    try {
      await apiRequest('/v1/assessments/' + id, { method: 'DELETE' }, true);
      if (epoch === generation.current) {
        if (pendingSave.current?.id === id) pendingSave.current = null;
        setNotice('Cloud snapshot deleted.');
        await load();
      }
    } catch (e) {
      if (epoch === generation.current) setError((e as Error).message);
    } finally {
      if (epoch === generation.current) setBusy(false);
    }
  }
  return (
    <section className="panel cloud-panel">
      <div className="chart-heading">
        <div>
          <h2>Private cloud workspace</h2>
          <p>Sign in to save assessments across devices.</p>
        </div>
        <span className="tag">Supabase</span>
      </div>
      {!cloudConfigured ? (
        <p>
          Cloud services are not configured in this deployment. Device storage
          and report export remain available.
        </p>
      ) : !ready ? (
        <p role="status">Restoring your session…</p>
      ) : !session ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void authenticate();
          }}
        >
          <div className="two-col">
            <label className="field">
              Email
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label className="field">
              Password
              <input
                type="password"
                required
                minLength={8}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          </div>
          <div className="output-actions">
            <Button type="submit" className="primary" disabled={busy}>
              Sign in
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={busy || !email || password.length < 8}
              onClick={() => void authenticate(true)}
            >
              Create account
            </Button>
          </div>
        </form>
      ) : (
        <>
          <div className="cloud-actions">
            <span>{session.user.email}</span>
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => void saveCloud()}
            >
              Save current assessment to cloud
            </Button>
            <Button variant="ghost" disabled={busy} onClick={() => void load()}>
              Refresh
            </Button>
            <Button
              variant="ghost"
              disabled={busy}
              onClick={async () => {
                const { error } = await getSupabase()!.auth.signOut();
                if (error) setError(error.message);
              }}
            >
              Sign out
            </Button>
          </div>
          {rows.length === 0 && !busy && (
            <p>
              No cloud assessments yet. Save the current assessment to create a
              private snapshot.
            </p>
          )}
          <ul className="cloud-records">
            {rows.map((row) => (
              <li key={row.id}>
                <div>
                  <b>{row.name}</b>
                  <small>
                    {new Date(row.created_at).toLocaleString()} · {row.method} ·
                    unreviewed
                  </small>
                </div>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => void open(row.id)}
                >
                  Open
                </Button>
                <Button
                  variant="ghost"
                  disabled={busy}
                  onClick={() => setRemove(row.id)}
                >
                  Delete
                </Button>
              </li>
            ))}
          </ul>
          {next && (
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => void load(next)}
            >
              Load more
            </Button>
          )}
        </>
      )}
      {busy && <p role="status">Working… Your current inputs are retained.</p>}
      {notice && (
        <p className="feedback" role="status">
          {notice}
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <AlertDialog
        open={!!remove}
        onOpenChange={(open) => {
          if (!open) setRemove(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete cloud snapshot?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes the snapshot from your account. Export a backup first
              if you need to retain it. Device copies remain unchanged.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (remove) void deleteRow(remove);
                setRemove(null);
              }}
            >
              Delete snapshot
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
