# FotoFlut — Architektur- & Umsetzungsplan

Immich-Alternative (Neubau), Docker/Unraid-gehostet, UI funktional/optisch nah an Immich.
Handy-Upload per **WebDAV** → Eingangsordner → Import-Worker.
Host: **Unraid** (Linux, Docker), **Intel Arc GPU** für ML über **OpenVINO** (`/dev/dri`), CPU-Fallback.
Ausgangspunkt: reale Bibliothek mit **~21.000 Bildern + Videos** → Video-Mitsupport und Timeline-Performance von Anfang an einplanen.
Zugang: **öffentlicher Reverse-Proxy** (vom Nutzer betrieben); `FF_BASE_URL` steuert alle generierten Links (Share-Links, EMBED-URLs). Der mitgelieferte Caddy ist optional (`proxy`-Profil).
Images: **ghcr.io/gottschalkfelix4-source/fotoflut** und **…/fotoflut-ml**, gebaut per GitHub Actions (`.github/workflows/docker.yml`).

---

## 1. Architektur (Docker Compose)

```
Handy (Autosync/FolderSync) ──WebDAV──▶ webdav-Container ──▶ ./upload/
                                                              │
                                             import-worker (chokidar + Reconcile-Scan)
                                                              ▼
Browser ◀── Reverse-Proxy (Nutzer) / Caddy ──▶ app (Fastify: REST + Web + Import/Worker-Jobs)
                                                  │  ▲
                                                  ▼  │
                                        postgres 16 (pgvector, pg_trgm)   redis ──▶ ml (Python + OpenVINO, Intel Arc /dev/dri)
```

### Services (`docker-compose.yml`)
| Service | Image/Bau | Zweck |
|---|---|---|
| `app` | `ghcr.io/gottschalkfelix4-source/fotoflut` | API, Auth, Web-UI, Import-/Verarbeitungs-Jobs |
| `ml` | `ghcr.io/gottschalkfelix4-source/fotoflut-ml` | ML-Inference; `devices: /dev/dri`, `group_add` render |
| `db` | `pgvector/pgvector:pg16` | Metadaten, pgvector + pg_trgm |
| `redis` | `redis:7-alpine` | BullMQ Queues |
| `webdav` | `hacdias/webdav` | Upload-Eingang (Per-User-Credentials aus Admin-UI) |
| `proxy` *(optional)* | `caddy:2` | Auto-TLS, nur mit `--profile proxy` |

### Pfade (Bind-Mounts; Unraid: Share-Disks, nicht Cache-Disk)
```
/data/library      Originale:  library/<userId>/<yyyy>/<MM>/<dd>/<hash>.<ext>
/data/derivatives  Thumbnails, Video-Transcodes, Gesichts-Crops
/data/upload       WebDAV-Eingang; nach Import → in library verschoben
/model-cache       ONNX/OpenVINO-Modelle   ./data/postgres, ./data/redis (Compose-Varianten)
```

## 2. Tech-Stack

- **Monorepo**: pnpm workspaces — `apps/api` (Node 24 + Fastify, TS nativ), `apps/web` (Next.js), `apps/ml` (Python), `packages/shared`
- **API**: Fastify (Platzhalter läuft), JWT Access/Refresh + API-Keys, RBAC (owner/admin), **BullMQ**, Swagger
- **DB**: Drizzle ORM + Migrationen; pgvector (HNSW), pg_trgm
- **Web**: Next.js (statischer Export, von app mit ausgeliefert) + Tailwind + shadcn/ui — Immich-Look (Timeline mit Sticky-Datumsheadern, Grid, Detail-Panel, dunkles Theme)
- **Bild/Video**: `sharp` (Thumbs 256/640/1536, Blurhash), `exifr`, `xxhash-wasm` (xxHash3-128 Dedupe), `ffprobe`/`ffmpeg` (Video-Metadaten, Poster, Transcode)
- **ML**: ONNX Runtime mit **OpenVINO EP** (`device=GPU`, Fallback `CPU`); SCRFD + ArcFace r100 (512-d, inkrementelles DBSCAN-Clustering), CLIP ViT-B/16 für Smart-Search
- **Karte**: Leaflet + OSM (Tile-URL konfigurierbar), Marker-Clustering

## 3. Datenmodell (Kerntabellen)

```
users (role, quota_bytes, storage_used, webdav_pass_hash)
assets (owner_id, library_path, checksum xxh3, type photo|video, duration,
        visibility, is_favorite, is_trashed, deleted_at, local_exif_date)
asset_exif (make/model/lens/focal/aperture/iso/lat/lng/country/...)
albums / album_assets (ordered, shared)
tags / asset_tags
persons / faces (bbox)         asset_embeddings vector(512)  -- CLIP
                               face_embeddings  vector(512)
share_links (slug, password?, expires_at, allow_download)
api_keys / job_logs / audit_logs
```
Indizes: HNSW auf Embeddings; `(owner_id, local_exif_date desc)` für Timeline (bei 21k Assets trivial); Trigramm auf Originalname/Tags.

## 4. API (Immich-artig unter `/api`)

`/authentication/*` · `/users` + `/admin/*` (Nutzer, Quota, Jobs, WebDAV-Credentials) · `/assets` (CRUD, trash, archive-zips) · `/albums` (+shared) · `/people` (merge/review) · `/search` `/search/smart` `/search/metadata` · `/shared-links` · `/tags` · `/timeline` (daily/monthly/yearly Buckets) · `/download/*` · `/server-info` · `/api-keys`
Alle generierten URLs hängen an `FF_BASE_URL`.

## 5. Import-Pipeline (WebDAV → Bibliothek)

1. Handy-App (Autosync o. ä.): `DCIM/Camera` → `/upload/<user>/`, one-way
2. `import-worker`: Watch + 5-min-Reconcile-Scan; halbgeschriebene Files via Size-Stable-Check; validiert Magic Bytes
3. xxHash3 → Dedupe → EXIF (bei Videos: ffprobe) → `mv` nach `/data/library` → DB → Jobs: thumbnail → clip → face (Priorität thumb > clip > face); Videos zusätzlich `transcode` (H.264/MP4 für Web-Playback; Original bleibt Download-Datei)
4. Fehler → `/upload/_quarantine/` + Admin-UI

## 6. UI-Seiten (Immich-orientiert)

- **Library** (Timeline, virtuelles Grid, Mehrfachauswahl, Favoriten, Trash), **Explore** (Karte/Alben/Personen/Tags), **Search** (Smart + Metadaten-Filter), Album-Editor, **People-Review** („das bin nicht ich“), **Admin** (Nutzer/Quota/WebDAV-Creds/Jobs/Storage/Settings inkl. ML-Device & Tile-Server), **Public Share** `/share/<slug>`
- Mobile: installierbare PWA (Phase 5)

## 7. Phasen & Status

| Phase | Inhalt | Status |
|---|---|---|
| **0 – Fundament** | Repo + Logo + CI/ghcr, Compose + Unraid-Templates, Drizzle, JWT-Auth | **Repo/Scaffold ✓**, Auth/DB folgen |
| **1 – Kern-Loop** | WebDAV + Import-Worker + Dedupe/EXIF/Video-Probe + Thumbnails + Timeline-UI + Asset-Detail | |
| **2 – Organisation** | Alben/shared Alben, Tags, Favoriten, Trash, pg_trgm-Suche, Metadaten-Suche | |
| **3 – ML** | OpenVINO/Arc-Pipeline, CLIP + pgvector Smart-Search, Gesichter + Clustering + People-UI | |
| **4 – Teilen & Multi-User** | Share-Links (Passwort/Expiry), Leaflet-Map, Quotas, Admin-Dashboard, WebDAV-Credential-UI | |
| **5 – Feinschliff** | PWA, Theme-Polish, Shortcuts, Blurhash-Fades, Backup-Doku | |

## 8. Intel Arc / OpenVINO

- Unraid-Host: Intel-Treiber im Kernel (i915/xe), Container bekommt `/dev/dri` (im Template via `--device /dev/dri --group-add render`)
- OpenVINO ≥ 2024.x; ONNX Runtime `providers=["OpenVINO"]`, `device="GPU"`; Modell-Konvertierung (SCRFD/ArcFace/CLIP) mit `optimum-intel`/OMZ → `/model-cache`
- **Risiko/Fallback**: Arc+OpenVINO ist der unwägbarste Pfad → `FF_ML_DEVICE=CPU` als dokumentierter Fallback; Auslastung via `intel_gpu_top` ins Job-Log

## 9. Sicherheit & Betrieb

- Reverse-Proxy terminiert TLS; `FF_BASE_URL` muss extern korrekt sein (Share-Links!)
- WebDAV nur über Proxy mit Auth; Basic-Auth-Passwörter pro User (Admin-UI), argon2 für Login-Passwörter, Rate-Limits
- Share-Links: Zufalls-Token + optional Passwort/Ablauf
- Backup: täglicher `pg_dump` + Anleitung Volume-Restore; `/data/upload` flüchtig, `/data/library` ist Master (Kopie der Originale via Unraid-Backup empfehlenswert)

## 10. Verifikation

- vitest: Import-Pipeline (Dedupe/Quarantäne), EXIF-Parsing, Timeline-Bucketing
- supertest: Auth, Asset-CRUD, Album-Sharing, Share-Link-Expiry
- Playwright: Login → Import simulieren → Timeline → Suche → Album → Share-Link
- ML-Golden-Set (~50 Referenzbilder) als Recall-Testjob; GPU-Nachweis per `intel_gpu_top`
- Smoke: `docker compose up -d --build`, Health-Endpoints, Share-Link hinter Proxy
