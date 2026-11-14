import clsx from "clsx";
import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "secondary" | "quiet";

interface StyleProps {
  variant?: Variant;
  small?: boolean; // 36px: only on the Reveal header and Host screen
  block?: boolean; // full width
}

const classes = ({ variant = "secondary", small, block }: StyleProps, extra?: string) =>
  clsx("cf-btn", `cf-btn--${variant}`, small && "cf-btn--sm", block && "cf-btn--block", extra);

/** A paper key that presses down on tap. One primary per screen. */
export function Button({
  variant,
  small,
  block,
  className,
  type = "button",
  ...rest
}: StyleProps & ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type={type} className={classes({ variant, small, block }, className)} {...rest} />;
}

/** Same look as Button, but navigates to another page. */
export function ButtonLink({
  href,
  children,
  variant,
  small,
  block,
  className,
}: StyleProps & { href: string; children: ReactNode; className?: string }) {
  return (
    <Link href={href} className={classes({ variant, small, block }, className)}>
      {children}
    </Link>
  );
}
