"use client";

import clsx from "clsx";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";
import { Button } from "./Button";
import { Stamp } from "./Stamp";

interface Props {
  name: string;
  url: string; // full link from the API, used as is
  joined: boolean;
  status?: string; // e.g. "Opened today's clue"
}

/** Link without the protocol, so people can type it. */
const shortLink = (url: string) => url.replace(/^https?:\/\//, "");

/** Invite card for the Host screen: name, a real QR of the link, "Joined" stamp. */
export function PlayerInvite({ name, url, joined, status }: Props) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard blocked: the link is printed on the card anyway.
    }
  }

  return (
    <article className={clsx("cf-invite", joined && "is-joined")}>
      <h3 className="cf-invite__name">{name}</h3>
      <div className="cf-invite__qr">
        <QRCodeSVG
          value={url}
          size={132}
          className="cf-qr"
          fgColor="currentColor"
          bgColor="transparent"
          role="img"
          aria-label={`QR code for ${name}'s link`}
        />
        {joined && <Stamp>Joined</Stamp>}
      </div>
      <p className="cf-invite__link">{shortLink(url)}</p>
      {status && <p className="cf-caption">{status}</p>}
      <Button variant="quiet" onClick={copy}>
        {copied ? "Copied" : "Copy link"}
      </Button>
    </article>
  );
}
