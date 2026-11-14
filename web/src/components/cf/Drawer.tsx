import clsx from "clsx";
import type { ReactNode } from "react";

interface Props {
  title: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  bodyClassName?: string;
  onToggle?: (open: boolean) => void;
}

/** A folded section on `folder-deep` that opens on tap (native <details>). */
export function Drawer({ title, children, defaultOpen, bodyClassName, onToggle }: Props) {
  return (
    <details
      className="cf-drawer"
      open={defaultOpen}
      onToggle={(e) => onToggle?.((e.currentTarget as HTMLDetailsElement).open)}
    >
      <summary>{title}</summary>
      <div className={clsx("cf-drawer__body", bodyClassName)}>{children}</div>
    </details>
  );
}
