# Deep Defend OS Frontend

Deep Defend OS is the operator-facing UI for a multi-modal detection pipeline. It is built to scan images, audio, and video with a console-style experience that favors speed, clarity, and high-trust output over generic dashboard behavior.

## Mission

This frontend handles the complete user journey:

- ingest media files
- warm up backend models when needed
- show scan progress in stages
- render final detection results with media-specific detail

The interface is intentionally focused. The main scan flow lives in one place, while supporting components handle upload, status, and result rendering.

## What You Get

- Multi-file upload for image, audio, and video scanning.
- Live model warmup and backend status visibility.
- Staged progress feedback with a JARVIS-style overlay.
- Rich result cards for image detections, audio ensemble output, and video analysis.
- Playback support for scanned audio files.

## Stack

- Vite
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Framer Motion
- React Router

## Local Run

```sh
npm install
npm run dev
```

The frontend expects the backend at `http://127.0.0.1:8001`.

## Scripts

- `npm run dev` - start the development server.
- `npm run build` - create the production bundle.
- `npm run preview` - preview the built app locally.
- `npm run lint` - run ESLint.
- `npm run test` - run the test suite.
- `npm run test:watch` - keep tests running in watch mode.

## Key Files

- `src/pages/Index.tsx` - scan orchestration, warmup flow, and result assembly.
- `src/components/ScanPanel.tsx` - file selection and scan trigger UI.
- `src/components/StatusPanel.tsx` - backend health and model state display.
- `src/components/ResultCard.tsx` - final output for image, audio, and video scans.
- `src/components/JarvisOverlay.tsx` - full-screen staged progress overlay.

## Backend Contract

The frontend talks to these backend endpoints:

- `POST /scan` - scan an uploaded file.
- `GET /model-status` - check model readiness.
- `POST /warmup-models` - preload models for the requested media types.
- `GET /audio-loading-status` - inspect audio ensemble loading state.
- `GET /health` - verify service availability.

## Design Notes

- Media uploads are only handled in the backend; the frontend stays focused on orchestration and presentation.
- Audio results can show ensemble breakdowns, voting, and probability averages.
- Video and image results use the same results surface, but each one renders its own detector-specific details.
- The UI is designed to feel deliberate: fast transitions, strong contrast, and operational feedback instead of generic app chrome.

## Build And Ship

```sh
npm run build
```

Serve the generated static assets from your preferred host and point the frontend to a reachable backend before deployment.
