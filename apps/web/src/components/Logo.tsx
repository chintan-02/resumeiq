export function Logo({ size = 24 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 26 26" aria-hidden="true">
      <rect x="1" y="1" width="24" height="24" rx="6" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M7 9h12M7 13h8M7 17h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="19" cy="17" r="2.5" fill="#0F6E5C" />
    </svg>
  );
}
