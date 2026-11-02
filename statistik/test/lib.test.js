import assert from 'node:assert/strict';
import { test } from 'node:test';
import { arBot, besokshash, dagarSedan, enhet, kallaFran, svenskDag, tolkaHandelse, verifieraToken } from '../src/lib.js';

test('sidvisning: frågesträng och ankare tas bort från sidan', () => {
  const h = tolkaHandelse({ t: 's', p: '/skal/iphone-17/?mejl=a@b.se#x', r: 'https://www.google.com/search?q=hemligt' });
  assert.equal(h.sida, '/skal/iphone-17/');
  assert.equal(h.kalla, 'google.com');
  assert.equal(JSON.stringify(h).includes('hemligt'), false);
});

test('ogiltiga händelser avvisas', () => {
  for (const d of [null, 1, {}, { t: 'x', p: '/' }, { t: 's' }, { t: 's', p: 'https://ond.se' }, { t: 'e', p: '/' }, { t: 's', p: 5 }]) {
    assert.equal(tolkaHandelse(d), null);
  }
});

test('långa värden kortas och kontrolltecken tas bort', () => {
  const h = tolkaHandelse({ t: 'e', p: '/', n: 'a\n'.repeat(100), v: 'b'.repeat(500) });
  assert.ok(h.namn.length <= 40 && !h.namn.includes('\n'));
  assert.equal(h.varde.length, 80);
});

test('egen webbplats räknas inte som källa', () => {
  assert.equal(kallaFran('https://corder.se/skal/', 'corder.se'), null);
  assert.equal(kallaFran('javascript:alert(1)', 'corder.se'), null);
  assert.equal(kallaFran('', 'corder.se'), null);
});

test('botar och enheter känns igen', () => {
  assert.ok(arBot('Mozilla/5.0 (compatible; Googlebot/2.1)'));
  assert.ok(arBot(''));
  assert.equal(arBot('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0) Safari/604.1'), false);
  assert.equal(enhet('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0) Mobile'), 'mobil');
  assert.equal(enhet('Mozilla/5.0 (iPad; CPU OS 18_0)'), 'surfplatta');
  assert.equal(enhet('Mozilla/5.0 (Macintosh; Intel Mac OS X)'), 'dator');
});

test('hashen byts med dagsnyckeln och avslöjar inte IP', async () => {
  const a = await besokshash('nyckel1', '1.2.3.4', 'ua');
  assert.equal(a, await besokshash('nyckel1', '1.2.3.4', 'ua'));
  assert.notEqual(a, await besokshash('nyckel2', '1.2.3.4', 'ua'));
  assert.equal(a.length, 16);
  assert.equal(a.includes('1.2.3.4'), false);
});

test('dygnet byts vid svensk midnatt', () => {
  assert.equal(svenskDag(new Date('2026-11-02T22:59:00Z')), '2026-11-02');
  assert.equal(svenskDag(new Date('2026-11-02T23:01:00Z')), '2026-11-03');
  assert.equal(dagarSedan('2026-03-01', 1), '2026-02-28');
});

test('token: bara rätt signatur, målgrupp, utfärdare och giltighet godkänns', async () => {
  const par = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
  const annan = await crypto.subtle.generateKey({ name: 'RSASSA-PKCS1-v1_5', modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: 'SHA-256' }, true, ['sign', 'verify']);
  const jwk = { ...(await crypto.subtle.exportKey('jwk', par.publicKey)), kid: 'k1' };
  const del = o => Buffer.from(JSON.stringify(o)).toString('base64url');
  const nu = 1_800_000_000;
  const signera = async (last, nyckel = par.privateKey, huvud = { alg: 'RS256', kid: 'k1' }) => {
    const d = `${del(huvud)}.${del(last)}`;
    const s = await crypto.subtle.sign('RSASSA-PKCS1-v1_5', nyckel, new TextEncoder().encode(d));
    return `${d}.${Buffer.from(s).toString('base64url')}`;
  };
  const kontroll = t => verifieraToken(t, { nycklar: [jwk], aud: 'aud1', utfardare: 'https://t.cloudflareaccess.com', nu });
  const bra = { aud: ['aud1'], iss: 'https://t.cloudflareaccess.com', exp: nu + 60 };
  assert.ok(await kontroll(await signera(bra)));
  assert.equal(await kontroll(await signera({ ...bra, aud: ['fel'] })), null);
  assert.equal(await kontroll(await signera({ ...bra, iss: 'https://ond' })), null);
  assert.equal(await kontroll(await signera({ ...bra, exp: nu - 1 })), null);
  assert.equal(await kontroll(await signera(bra, annan.privateKey)), null);
  assert.equal(await kontroll(await signera(bra, par.privateKey, { alg: 'none', kid: 'k1' })), null);
  assert.equal(await kontroll('skräp'), null);
});

test('portalen är stängd utan giltig inloggning', async () => {
  const { default: admin } = await import('../src/admin.js');
  const dag = u => admin.fetch(new Request(u), {});
  assert.equal((await dag('https://corder-admin.exempel.workers.dev/')).status, 403);
  assert.equal((await dag('https://corder-admin.exempel.workers.dev/api/rapport')).status, 403);
  assert.equal((await dag('https://corder-admin.exempel.workers.dev/export.csv')).status, 403);
  // Den lokala genvägen får aldrig gälla på en publik adress.
  const r = await admin.fetch(new Request('https://corder-admin.exempel.workers.dev/'), { LOKAL_UTAN_INLOGGNING: 'ja' });
  assert.equal(r.status, 403);
  const skrap = await admin.fetch(new Request('https://x.workers.dev/', { headers: { 'Cf-Access-Jwt-Assertion': 'skräp' } }), {});
  assert.equal(skrap.status, 403);
});

test('insamlingen avvisar främmande ursprung och svarar utan att ta emot annat', async () => {
  const { default: ins } = await import('../src/insamling.js');
  const env = { TILLATNA_URSPRUNG: 'https://corder.se' };
  const ctx = { waitUntil() {} };
  const r = await ins.fetch(new Request('https://x.workers.dev/e', { method: 'POST', headers: { Origin: 'https://ond.se' }, body: '{}' }), env, ctx);
  assert.equal(r.status, 403);
  const ok = await ins.fetch(new Request('https://x.workers.dev/e', { method: 'POST', headers: { Origin: 'https://corder.se' }, body: '{}' }), env, ctx);
  assert.equal(ok.status, 204);
  assert.equal(ok.headers.get('Access-Control-Allow-Origin'), 'https://corder.se');
  assert.equal(ok.headers.has('Set-Cookie'), false);
  assert.equal((await ins.fetch(new Request('https://x.workers.dev/annat'), env, ctx)).status, 404);
});

test('insamlingen läser innehållet innan svaret skickas', async () => {
  const { default: ins } = await import('../src/insamling.js');
  const req = new Request('https://x.workers.dev/e', { method: 'POST', headers: { Origin: 'https://corder.se' }, body: '{}' });
  await ins.fetch(req, { TILLATNA_URSPRUNG: 'https://corder.se' }, { waitUntil() {} });
  assert.equal(req.bodyUsed, true);
});

test('formulär: giltiga ärenden godkänns och fel stoppas', async () => {
  const { tolkaArende, arRobotformular } = await import('../src/lib.js');
  const bas = { typ: 'ansokan', foretag: 'Kiosken', kontakt: 'Kim', epost: 'kim@kiosken.se', tid: 9000 };
  assert.equal(tolkaArende(bas).foretag, 'Kiosken');
  assert.equal(tolkaArende({ ...bas, typ: 'annat' }), null);
  assert.equal(tolkaArende({ ...bas, epost: 'inte-en-adress' }), null);
  assert.equal(tolkaArende({ ...bas, epost: 'a"b@x.se' }), null);
  assert.equal(tolkaArende({ ...bas, foretag: '  ' }), null);
  const best = { ...bas, typ: 'bestallning', rader: [{ ean: '7350140690283', artikel: 'Kabel', antal: 5 }] };
  assert.deepEqual(JSON.parse(tolkaArende(best).rader), best.rader);
  assert.equal(tolkaArende({ ...best, leverans: 'Storgatan 1', meddelande: 'Hej' }).meddelande, 'Leverans: Storgatan 1\nHej');
  assert.equal(tolkaArende({ ...best, rader: [] }), null);
  assert.equal(tolkaArende({ ...best, rader: [{ ean: 'abc', antal: 5 }] }), null);
  assert.equal(tolkaArende({ ...best, rader: [{ ean: '7350140690283', antal: 0 }] }), null);
  assert.equal(tolkaArende({ ...best, rader: Array(151).fill(best.rader[0]) }), null);
  assert.equal(arRobotformular({ ...bas, webbplats: 'x' }), true);
  assert.equal(arRobotformular({ ...bas, tid: 500 }), true);
  assert.equal(arRobotformular(bas), false);
});

test('formulär: främmande ursprung nekas och robotfällan sparar inget', async () => {
  const { default: ins } = await import('../src/insamling.js');
  let sparat = 0;
  const env = { TILLATNA_URSPRUNG: 'https://corder.se', DB: new Proxy({}, { get() { sparat++; throw new Error('databasen ska inte användas'); } }) };
  const ctx = { waitUntil() {} };
  const post = (origin, kropp) => ins.fetch(new Request('https://x.workers.dev/f', { method: 'POST', headers: { Origin: origin, 'User-Agent': 'Mozilla/5.0' }, body: JSON.stringify(kropp) }), env, ctx);
  assert.equal((await post('https://ond.se', {})).status, 403);
  assert.equal((await post('https://corder.se', { typ: 'ansokan', webbplats: 'spam' })).status, 201);
  assert.equal((await post('https://corder.se', { typ: 'annat', tid: 9000 })).status, 400);
  assert.equal(sparat, 0);
});

test('portalens ändringar kräver inloggning och egen begäran', async () => {
  const { default: admin } = await import('../src/admin.js');
  const utan = await admin.fetch(new Request('https://x.workers.dev/api/arenden/1', { method: 'DELETE' }), {});
  assert.equal(utan.status, 403);
  const lista = await admin.fetch(new Request('https://x.workers.dev/api/arenden'), {});
  assert.equal(lista.status, 403);
  let anvand = 0;
  const env = { LOKAL_UTAN_INLOGGNING: 'ja', DB: new Proxy({}, { get() { anvand++; throw new Error('nej'); } }) };
  const frammande = await admin.fetch(new Request('http://localhost:8788/api/arenden/1', { method: 'DELETE', headers: { Origin: 'https://ond.se', 'Content-Type': 'application/json' } }), env);
  assert.equal(frammande.status, 403);
  assert.equal(anvand, 0);
});

test('portalens lösenord: fel och korta lösenord släpps inte in', async () => {
  const { default: admin } = await import('../src/admin.js');
  const losen = 'ett-langt-slumpat-losenord-for-test';
  const basic = v => ({ Authorization: `Basic ${btoa(v)}` });
  const db = { prepare: () => ({ all: async () => ({ results: [] }) }) };
  const be = (headers, env = { PORTAL_LOSENORD: losen, DB: db }) => admin.fetch(new Request('https://x.workers.dev/api/arenden', { headers }), env);
  const utan = await be({});
  assert.equal(utan.status, 401);
  assert.match(utan.headers.get('WWW-Authenticate'), /^Basic/);
  assert.equal((await be(basic('corder:fel'))).status, 401);
  assert.equal((await be({ Authorization: 'Basic %%%' })).status, 401);
  assert.equal((await be(basic(`corder:${losen}`))).status, 200);
  assert.equal((await be(basic('corder:kort'), { PORTAL_LOSENORD: 'kort', DB: db })).status, 401);
});
