import Fastify from 'fastify';

// Phase-0-Platzhalter: wird in Phase 1 durch Auth, Assets, Timeline usw. ersetzt.
const PORT = Number(process.env.PORT ?? 8080);
const BASE_URL = process.env.FF_BASE_URL ?? 'http://localhost:8080';

const app = Fastify({ logger: true });

app.get('/healthz', async () => ({ status: 'ok' }));

app.get('/api/server-info', async () => ({
  app: 'fotoflut',
  version: process.env.FF_VERSION ?? '0.0.1-dev',
  baseUrl: BASE_URL,
  phase: 'phase-0-scaffold',
}));

app
  .listen({ port: PORT, host: '0.0.0.0' })
  .then(() => app.log.info(`fotoflut api listening on :${PORT} (base url: ${BASE_URL})`))
  .catch((err) => {
    app.log.error(err);
    process.exit(1);
  });
