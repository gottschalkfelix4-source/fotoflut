<div align="center">
  <img src="docs/logo.png" alt="Fotoflut Logo" width="140"/>
  <h1>Fotoflut</h1>
  <p><strong>Self-hostete Foto-Cloud als Immich-Alternative — mit WebDAV-Upload, Gesichts-CLustering und semantischer Suche.</strong></p>

  [![Lizenz: AGPL-3.0](https://img.shields.io/badge/Lizenz-AGPL--3.0-blue.svg)](LICENSE)
  [![Docker Images](https://github.com/gottschalkfelix4-source/fotoflut/actions/workflows/docker.yml/badge.svg)](https://github.com/gottschalkfelix4-source/fotoflut/actions/workflows/docker.yml)
</div>

---

> ⚠️ **Frühes Projekt (Phase 0/1).** Scaffold, Container und Pipelines sind lauffähig; die Kernfeatures entstehen schrittweise nach [docs/PLAN.md](docs/PLAN.md).

## Features (geplant / in Arbeit)

- 📅 **Timeline** nach EXIF-Datum mit Tages-/Monats-/Jahresgruppen, Favoriten, Papierkorb
- 📤 **Upload per WebDAV** vom Handy (Autosync, FolderSync, DAVx5) → automatischer Import mit Dedupe (xxHash3) und EXIF-PIndex
- 🖼️ **Alben, geteilte Alben, Stichwörter**, Video-Mitsupport (~21.000 Assets realer Bibliotheks-Testfall)
- 🧠 **ML**: Gesichts-Erkennung & -Clustering (SCRFD + ArcFace) und semantische Suche (CLIP + pgvector) — **Intel Arc GPU via OpenVINO**, CPU-Fallback
- 🔗 **Share-Links** (Passwort/Ablauf), **Karte** (Leaflet+OSM), Multi-User mit Quotas + Admin-UI
- 🐳 **Docker Compose** oder **Unraid** (CA-Templates vorhanden)

## Schnellstart (Docker Compose)

```bash
git clone https://github.com/gottschalkfelix4-source/fotoflut.git
cd fotoflut
cp .env.example .env        # Passwörter/Domain setzen
docker compose up -d --build
# Web-UI:  http://localhost:8080   (Platzhalter-API bis Phase 1)
```

Der eigene Reverse-Proxy (zwangfrei): einfach den `proxy`-Service (Caddy) weglassen oder nutzen und `FF_BASE_URL` auf die externe URL setzen — sie steuert alle generierten Links (Share-Links, Thumbnails in E-Mails usw.).

## Unraid

1. **Empfohlen: Docker Compose** (Unraid 6.12+): Ordner `/boot/config/...` bzw. UI → *Docker → Compose*, diese `docker-compose.yml` + `.env` eintragen. Pfade (`FF_LIBRARY_DIR` …) auf `Share-Disks` zeigen lassen (Cache-Disks vermeiden).
2. **Community Applications:** Templates aus diesem Repo hinzufügen (Settings → *Add New Location*):

   ```
   https://raw.githubusercontent.com/gottschalkfelix4-source/fotoflut/main/unraid/
   ```

   → **Fotoflut** (App) und **Fotoflut-ML** (GPU-Worker, benötigt `/dev/dri`) erscheinen in CA. Dazu je einen PostgreSQL- und Redis-Container (bestehende CA-Templates) im gleichen benutzerdefinierten Netzwerk starten.

## Umgebungsvariablen

| Variable | Bedeutung | Beispiel |
|---|---|---|
| `FF_BASE_URL` | Öffentliche Basis-URL (hinter Reverse-Proxy!) | `https://fotos.example.de` |
| `FF_DOMAIN` | Domain für den mitgelieferten Caddy (`proxy`-Profil) | `fotos.example.de` |
| `POSTGRES_PASSWORD` | DB-Passwort | — |
| `FF_ML_DEVICE` | `GPU` (Intel Arc) oder `CPU` | `GPU` |
| `FF_LIBRARY_DIR` / `FF_DERIV_DIR` / `FF_UPLOAD_DIR` | Bind-Mounts: Originaldateien, Thumbnails/Derivate, WebDAV-Eingang | `/mnt/user/Fotoflut/library` |
| `FF_MODEL_CACHE` | Cache für ONNX/OpenVINO-Modelle | `/mnt/user/Fotoflut/model-cache` |

## WebDAV-Upload einrichten (Handy)

Der `webdav`-Service mountet `FF_UPLOAD_DIR`. Eine App wie **Autosync (WebDAV)** oder **FolderSync** richtet man auf `https://<FF_BASE_URL-Host>/dav/` bzw. Port `6065`, Credentials aus `config/webdav/config.yml` (später: pro User aus der Admin-UI). Dateien von dort importiert der Worker automatisch in die Bibliothek.

## Beteiligte Container

| Service | Image | Zweck |
|---|---|---|
| `app` | `ghcr.io/gottschalkfelix4-source/fotoflut` | API + Web-UI + Worker |
| `ml` | `ghcr.io/gottschalkfelix4-source/fotoflut-ml` | ML-Inference (OpenVINO, Intel Arc) |
| `db` | `pgvector/pgvector:pg16` | PostgreSQL + Vektorsuche |
| `redis` | `redis:7-alpine` | Job-Queues |
| `webdav` | `hacdias/webdav` | Upload-Eingang |
| `proxy` *(optional)* | `caddy:2` | Auto-TLS, Profil `proxy` |

## Entwicklung

```bash
pnpm install
pnpm api:dev        # API auf :8080 (Node 24, TypeScript nativ)
```

Der komplette Architektur-, Datenmodell- und Phasenplan liegt in [docs/PLAN.md](docs/PLAN.md).

## Lizenz

[AGPL-3.0](LICENSE) — wie Immich: Network-Derivate müssen die Source offenlegen.
