import { Fragment, type ReactNode } from "react";

/**
 * Minimal, safe markdown for model replies: **bold**, *italic* / _italic_, `code`, "- " and "1. " lists,
 * and line breaks. It builds React elements (no HTML injection), so model output can't add markup.
 */
export default function RichText({ text, className }: { text: string; className?: string }) {
  const blocks: ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;
  let para: string[] = [];

  const flushPara = () => {
    if (para.length) blocks.push(<p key={blocks.length}>{inlineLines(para)}</p>);
    para = [];
  };
  const flushList = () => {
    if (!list) return;
    const items = list.items.map((it, i) => <li key={i}>{inline(it)}</li>);
    blocks.push(
      list.ordered ? (
        <ol key={blocks.length} className="list-decimal space-y-0.5 pl-5">{items}</ol>
      ) : (
        <ul key={blocks.length} className="list-disc space-y-0.5 pl-5">{items}</ul>
      ),
    );
    list = null;
  };

  for (const raw of text.replace(/\r\n/g, "\n").split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    if (bullet || numbered) {
      flushPara();
      const ordered = !!numbered;
      if (!list || list.ordered !== ordered) {
        flushList();
        list = { ordered, items: [] };
      }
      list.items.push((bullet || numbered)![1]);
    } else if (!line) {
      flushPara();
      flushList();
    } else {
      flushList();
      para.push(line.replace(/^#{1,6}\s+/, "")); // headings read as plain lines in a chat bubble
    }
  }
  flushPara();
  flushList();
  return <div className={`space-y-2 ${className ?? ""}`}>{blocks}</div>;
}

function inlineLines(lines: string[]): ReactNode[] {
  return lines.map((l, i) => (
    <Fragment key={i}>
      {i > 0 && <br />}
      {inline(l)}
    </Fragment>
  ));
}

const TOKEN = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\*[^*\s][^*]*\*|_[^_\s][^_]*_)/g;

function inline(s: string): ReactNode[] {
  return s.split(TOKEN).map((part, i) => {
    if (!part) return null;
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__")))
      return <strong key={i} className="font-extrabold">{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`"))
      return <code key={i} className="rounded bg-surface-2 px-1 text-[0.95em]">{part.slice(1, -1)}</code>;
    if ((part.startsWith("*") && part.endsWith("*")) || (part.startsWith("_") && part.endsWith("_")))
      return <em key={i}>{part.slice(1, -1)}</em>;
    return <Fragment key={i}>{part}</Fragment>;
  });
}

/** For one-line spots (cards, toasts): drop markdown markers instead of rendering them. */
export function plainText(s: string): string {
  return s.replace(/\*\*([^*]+)\*\*|__([^_]+)__/g, "$1$2").replace(/`([^`]+)`/g, "$1").replace(/(^|\s)[*_]([^*_\s][^*_]*)[*_]/g, "$1$2");
}
