import type { SVGProps } from "react";

function Icon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="sidebar__icon"
      {...props}
    />
  );
}

export function DashboardIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </Icon>
  );
}

export function UsersIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <circle cx="9" cy="8" r="3.2" />
      <path d="M2.5 20c1-3.6 3.6-5.5 6.5-5.5s5.5 1.9 6.5 5.5" />
      <circle cx="17.5" cy="8.5" r="2.3" />
      <path d="M15.7 14.7c2.4.2 4.3 2 5.1 4.8" />
    </Icon>
  );
}

export function GridIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <rect x="3" y="3" width="8" height="8" rx="1.5" />
      <rect x="13" y="3" width="8" height="8" rx="1.5" />
      <rect x="3" y="13" width="8" height="8" rx="1.5" />
      <rect x="13" y="13" width="8" height="8" rx="1.5" />
    </Icon>
  );
}

export function TrendIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M3 17 9 11l4 4 8-8" />
      <path d="M15 7h6v6" />
    </Icon>
  );
}

export function WalletIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <rect x="2.5" y="6" width="19" height="13" rx="2.2" />
      <path d="M2.5 10h19" />
      <circle cx="16.5" cy="14.2" r="1.3" fill="currentColor" stroke="none" />
    </Icon>
  );
}

export function UploadIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <path d="M12 16V4" />
      <path d="M6.5 9.5 12 4l5.5 5.5" />
      <path d="M4 16.5v2.3A2.2 2.2 0 0 0 6.2 21h11.6a2.2 2.2 0 0 0 2.2-2.2v-2.3" />
    </Icon>
  );
}

export function BuildingIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props}>
      <rect x="4" y="3" width="12" height="18" rx="1.2" />
      <path d="M16 8h4v13h-4" />
      <path d="M7.5 7h1M11.5 7h1M7.5 11h1M11.5 11h1M7.5 15h1M11.5 15h1" />
    </Icon>
  );
}

export function ChevronDownIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props} className="">
      <path d="m6 9 6 6 6-6" />
    </Icon>
  );
}

export function EyeIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props} className="" width={18} height={18}>
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </Icon>
  );
}

export function EyeOffIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <Icon {...props} className="" width={18} height={18}>
      <path d="M3 3l18 18" />
      <path d="M10.6 5.2A10.6 10.6 0 0 1 12 5c6.4 0 10 7 10 7a15.6 15.6 0 0 1-3.4 4.3M6.5 6.6C3.6 8.3 2 12 2 12s3.6 7 10 7a9.7 9.7 0 0 0 3.4-.6" />
      <path d="M9.5 10a3 3 0 0 0 4.2 4.2" />
    </Icon>
  );
}
