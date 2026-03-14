"use client";

import { useEffect, useRef } from "react";
import type { AssetListItem } from "@/lib/api";

declare global {
  interface Window {
    L?: {
      map: (element: HTMLElement, options?: Record<string, unknown>) => LeafletMap;
      tileLayer: (url: string, options?: Record<string, unknown>) => LeafletLayer;
      layerGroup: () => LeafletLayerGroup;
      circleMarker: (latlng: [number, number], options?: Record<string, unknown>) => LeafletMarker;
      latLngBounds: (points: [number, number][]) => { isValid: () => boolean };
    };
  }
}

type LeafletMap = {
  setView: (center: [number, number], zoom: number) => void;
  fitBounds: (bounds: { isValid: () => boolean }, options?: Record<string, unknown>) => void;
  remove: () => void;
};

type LeafletLayer = {
  addTo: (map: LeafletMap) => void;
};

type LeafletLayerGroup = {
  addTo: (map: LeafletMap) => LeafletLayerGroup;
  clearLayers: () => void;
};

type LeafletMarker = {
  addTo: (group: LeafletLayerGroup) => LeafletMarker;
  bindTooltip: (html: string, options?: Record<string, unknown>) => LeafletMarker;
  on: (event: string, handler: () => void) => LeafletMarker;
};

const LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
const LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";

let leafletPromise: Promise<typeof window.L> | null = null;

function ensureLeaflet() {
  if (typeof window === "undefined") return Promise.resolve(undefined);
  if (window.L) return Promise.resolve(window.L);
  if (leafletPromise) return leafletPromise;

  leafletPromise = new Promise((resolve, reject) => {
    if (!document.querySelector(`link[href="${LEAFLET_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = LEAFLET_CSS;
      document.head.appendChild(link);
    }

    const existing = document.querySelector(`script[src="${LEAFLET_JS}"]`) as HTMLScriptElement | null;
    if (existing) {
      existing.addEventListener("load", () => resolve(window.L));
      existing.addEventListener("error", () => reject(new Error("Could not load Leaflet")));
      return;
    }

    const script = document.createElement("script");
    script.src = LEAFLET_JS;
    script.async = true;
    script.onload = () => resolve(window.L);
    script.onerror = () => reject(new Error("Could not load Leaflet"));
    document.body.appendChild(script);
  });

  return leafletPromise;
}

export function PlacesMap({
  items,
  selectedId,
  onSelect,
  mode,
}: {
  items: AssetListItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  mode: "selected" | "all" | "folder";
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const groupRef = useRef<LeafletLayerGroup | null>(null);
  const lastBoundsKeyRef = useRef<string | null>(null);
  const lastModeRef = useRef<"selected" | "all" | "folder" | null>(null);

  useEffect(() => {
    let cancelled = false;

    ensureLeaflet()
      .then((L) => {
        if (!L || cancelled || !hostRef.current) return;
        if (!mapRef.current) {
          mapRef.current = L.map(hostRef.current, { zoomControl: true });
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          }).addTo(mapRef.current);
          groupRef.current = L.layerGroup().addTo(mapRef.current);
        }

        const map = mapRef.current;
        const group = groupRef.current;
        if (!map || !group) return;

        group.clearLayers();

        const points = items
          .filter((item) => item.lat != null && item.lon != null)
          .map((item) => ({
            id: item.id,
            lat: item.lat as number,
            lon: item.lon as number,
            label: item.filename,
          }));

        for (const point of points) {
          const active = point.id === selectedId;
          L.circleMarker([point.lat, point.lon], {
            radius: active ? 10 : 8,
            color: active ? "#8d6327" : "#55738f",
            weight: 2,
            fillColor: active ? "#c58a39" : "#7aa1c4",
            fillOpacity: 0.9,
            interactive: true,
          })
            .addTo(group)
            .bindTooltip(point.label, { direction: "top" })
            .on("click", () => onSelect(point.id));
        }

        if (points.length === 0) return;

        const selectedPoint = points.find((point) => point.id === selectedId) ?? points[0];
        if (mode === "selected") {
          lastBoundsKeyRef.current = null;
          lastModeRef.current = mode;
          map.setView([selectedPoint.lat, selectedPoint.lon], 13);
          return;
        }

        const boundsKey = points.map((point) => `${point.id}:${point.lat.toFixed(4)}:${point.lon.toFixed(4)}`).join("|");
        if (points.length === 1) {
          map.setView([selectedPoint.lat, selectedPoint.lon], 13);
          lastBoundsKeyRef.current = boundsKey;
          lastModeRef.current = mode;
          return;
        }
        if (boundsKey !== lastBoundsKeyRef.current || lastModeRef.current !== mode) {
          const bounds = L.latLngBounds(points.map((point) => [point.lat, point.lon] as [number, number]));
          if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [28, 28] });
          }
          lastBoundsKeyRef.current = boundsKey;
          lastModeRef.current = mode;
        }
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [items, mode, onSelect, selectedId]);

  useEffect(() => {
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
      groupRef.current = null;
    };
  }, []);

  return <div ref={hostRef} className="h-[420px] w-full" />;
}
