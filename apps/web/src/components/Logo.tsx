export function Logo({ size = 28 }: { size?: number }) {
  return (
    <span
      aria-hidden="true"
      className="flex items-center justify-center rounded-lg bg-mint"
      style={{ width: size, height: size }}
    >
      <svg width={size * 0.57} height={size * 0.57} viewBox="0 0 24 24" fill="none" stroke="#0a0c10" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 12l4 4L19 6" />
      </svg>
    </span>
  );
}
