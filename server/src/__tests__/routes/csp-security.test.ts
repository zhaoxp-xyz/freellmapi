import { describe, it, expect, beforeAll } from 'vitest';
import type { Express } from 'express';
import { createApp } from '../../app.js';
import { initDb } from '../../db/index.js';

async function getHeaders(app: Express, path: string): Promise<Headers> {
  const server = app.listen(0);
  const addr = server.address() as any;
  const res = await fetch(`http://127.0.0.1:${addr.port}${path}`);
  server.close();
  return res.headers;
}

describe('CSP security headers', () => {
  let app: Express;

  beforeAll(() => {
    process.env.ENCRYPTION_KEY = '0'.repeat(64);
    initDb(':memory:');
    app = createApp();
  });

  it('sets the Content-Security-Policy header on every response', async () => {
    const headers = await getHeaders(app, '/api/ping');
    const csp = headers.get('content-security-policy');
    expect(csp).toBeTruthy();
  });

  it('restricts default-src to self', async () => {
    const headers = await getHeaders(app, '/api/ping');
    const csp = headers.get('content-security-policy')!;
    expect(csp).toContain("default-src 'self'");
  });

  it('restricts script-src to self', async () => {
    const headers = await getHeaders(app, '/api/ping');
    const csp = headers.get('content-security-policy')!;
    expect(csp).toContain("script-src 'self'");
  });

  it('allows inline styles for React hydration', async () => {
    const headers = await getHeaders(app, '/api/ping');
    const csp = headers.get('content-security-policy')!;
    expect(csp).toContain("style-src 'self' 'unsafe-inline'");
  });

  it('does not set HSTS (local-only proxy)', async () => {
    const headers = await getHeaders(app, '/api/ping');
    expect(headers.get('strict-transport-security')).toBeNull();
  });

  it('does NOT emit upgrade-insecure-requests (HTTP-only LAN proxy)', async () => {
    // helmet's default directives include upgrade-insecure-requests, which
    // forces every asset request to https:// and breaks the dashboard when
    // reached via a LAN IP (192.168.x.x → ERR_SSL_PROTOCOL_ERROR → blank
    // page). The app must opt out via useDefaults:false.
    const headers = await getHeaders(app, '/api/ping');
    const csp = headers.get('content-security-policy')!;
    expect(csp).not.toContain('upgrade-insecure-requests');
  });

  it('whitelists the inline theme script via sha256 hash', async () => {
    // client/index.html ships an inline <script> (theme init before first
    // paint). With script-src 'self' that script is blocked unless its hash is
    // present. The app computes hashes from the built index.html at startup.
    const headers = await getHeaders(app, '/api/ping');
    const csp = headers.get('content-security-policy')!;
    expect(csp).toMatch(/script-src 'self'(?: 'sha256-[A-Za-z0-9+/=]+')+/);
  });
});
