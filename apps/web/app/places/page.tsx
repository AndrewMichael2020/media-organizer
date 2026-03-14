export default function PlacesPage() {
  return (
    <EmptyState
      label="Places"
      description="Geographic clusters and place candidates will appear here once extraction runs."
    />
  );
}

function EmptyState({ label, description }: { label: string; description: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-8">
      <p className="text-[11px] tracking-[0.2em] uppercase font-medium text-[hsl(var(--muted))]">{label}</p>
      <p className="text-[12px] text-[hsl(var(--muted-foreground))] max-w-xs leading-relaxed">{description}</p>
    </div>
  );
}
