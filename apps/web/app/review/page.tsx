export default function ReviewPage() {
  return (
    <EmptyState
      label="Review"
      description="Duplicate clusters, OCR-rich items, and metadata conflicts will be queued here."
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
