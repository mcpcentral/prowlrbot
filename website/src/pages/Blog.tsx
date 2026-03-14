import { useState, useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import {
  ArrowLeft,
  Calendar,
  User,
  Clock,
} from "lucide-react";
import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import type { SiteConfig } from "../config";
import { type Lang } from "../i18n";

interface BlogMeta {
  slug: string;
  title: string;
  date: string;
  author: string;
  tags: string[];
  summary: string;
  readTime: string;
}

interface BlogPost extends BlogMeta {
  content: string;
}

/** Known blog post filenames — ordered newest first. */
const BLOG_FILES = [
  "2026-03-11-pip-install-broke-my-wsl.md",
  "2026-03-10-whats-coming-next.md",
  "2026-03-10-war-room-is-live.md",
  "2026-03-10-setting-up-your-first-swarm.md",
  "2026-03-10-security-first.md",
  "2026-03-10-introducing-prowlrbot.md",
];

function fileToSlug(filename: string): string {
  return filename.replace(/\.md$/, "");
}

function parseFrontmatter(raw: string): { meta: Omit<BlogMeta, "slug" | "readTime">; body: string } {
  const match = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) return { meta: { title: "", date: "", author: "", tags: [], summary: "" }, body: raw };

  const fm = match[1];
  const body = match[2];

  const get = (key: string): string => {
    const m = fm.match(new RegExp(`^${key}:\\s*"?(.+?)"?\\s*$`, "m"));
    return m ? m[1] : "";
  };

  const tagsMatch = fm.match(/^tags:\s*\[(.+)\]\s*$/m);
  const tags = tagsMatch
    ? tagsMatch[1].split(",").map((t) => t.trim().replace(/['"]/g, ""))
    : [];

  return {
    meta: {
      title: get("title"),
      date: get("date"),
      author: get("author"),
      tags,
      summary: get("summary"),
    },
    body,
  };
}

function estimateReadTime(text: string): string {
  const words = text.split(/\s+/).length;
  const minutes = Math.max(1, Math.round(words / 200));
  return `${minutes} min read`;
}

const TAG_COLORS: Record<string, string> = {
  launch: "#00d4aa",
  vision: "#7c6cff",
  guide: "#f5a623",
  update: "#4fc3f7",
  "deep-dive": "#ff6b9d",
  alert: "#ff5252",
};

function TagBadge({ tag }: { tag: string }) {
  const color = TAG_COLORS[tag] || "var(--accent)";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.25rem",
        padding: "0.125rem 0.5rem",
        fontSize: "0.6875rem",
        fontWeight: 600,
        color,
        background: `${color}18`,
        borderRadius: "1rem",
        border: `1px solid ${color}30`,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      {tag}
    </span>
  );
}

function BlogList({ posts }: { posts: BlogMeta[] }) {
  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <div style={{ marginBottom: "var(--space-5)" }}>
        <h1
          style={{
            fontSize: "2.25rem",
            fontWeight: 800,
            color: "var(--text)",
            marginBottom: "var(--space-2)",
          }}
        >
          Blog
        </h1>
        <p
          style={{
            fontSize: "1.0625rem",
            color: "var(--text-muted)",
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          Engineering updates, deep dives, and the occasional war story from the
          ProwlrBot team.
        </p>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
        {posts.map((post) => (
          <Link
            key={post.slug}
            to={`/blog/${post.slug}`}
            className="blog-card"
            style={{
              display: "block",
              padding: "var(--space-4)",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "0.75rem",
              textDecoration: "none",
              transition: "all 0.2s ease",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-2)",
                marginBottom: "var(--space-2)",
                flexWrap: "wrap",
              }}
            >
              {post.tags.map((tag) => (
                <TagBadge key={tag} tag={tag} />
              ))}
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.25rem",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                  opacity: 0.7,
                }}
              >
                <Calendar size={12} />
                {post.date}
              </span>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.25rem",
                  fontSize: "0.75rem",
                  color: "var(--text-muted)",
                  opacity: 0.7,
                }}
              >
                <Clock size={12} />
                {post.readTime}
              </span>
            </div>
            <h2
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: "var(--text)",
                margin: "0 0 0.5rem 0",
                lineHeight: 1.3,
              }}
            >
              {post.title}
            </h2>
            <p
              style={{
                fontSize: "0.875rem",
                color: "var(--text-muted)",
                margin: 0,
                lineHeight: 1.6,
              }}
            >
              {post.summary}
            </p>
            <div
              style={{
                marginTop: "var(--space-2)",
                display: "flex",
                alignItems: "center",
                gap: "0.375rem",
                fontSize: "0.75rem",
                color: "var(--text-muted)",
                opacity: 0.6,
              }}
            >
              <User size={12} />
              {post.author}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function BlogPostView({ post }: { post: BlogPost }) {
  return (
    <div style={{ maxWidth: 720, margin: "0 auto" }}>
      <Link
        to="/blog"
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.375rem",
          fontSize: "0.8125rem",
          color: "var(--accent)",
          textDecoration: "none",
          marginBottom: "var(--space-3)",
        }}
        className="blog-back-link"
      >
        <ArrowLeft size={14} />
        All posts
      </Link>

      <div style={{ marginBottom: "var(--space-4)" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-2)",
            marginBottom: "var(--space-2)",
            flexWrap: "wrap",
          }}
        >
          {post.tags.map((tag) => (
            <TagBadge key={tag} tag={tag} />
          ))}
        </div>
        <h1
          style={{
            fontSize: "2rem",
            fontWeight: 800,
            color: "var(--text)",
            lineHeight: 1.2,
            margin: "0 0 var(--space-2) 0",
          }}
        >
          {post.title}
        </h1>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
            fontSize: "0.8125rem",
            color: "var(--text-muted)",
            flexWrap: "wrap",
          }}
        >
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.375rem" }}>
            <User size={14} />
            {post.author}
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.375rem" }}>
            <Calendar size={14} />
            {post.date}
          </span>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "0.375rem" }}>
            <Clock size={14} />
            {post.readTime}
          </span>
        </div>
      </div>

      <div className="docs-content blog-content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight, rehypeRaw]}
        >
          {post.content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

interface BlogProps {
  config: SiteConfig;
  lang: Lang;
  theme: "dark" | "light";
  onThemeToggle: () => void;
}

export function Blog({ config, lang, theme, onThemeToggle }: BlogProps) {
  const { slug } = useParams<{ slug?: string }>();
  const [posts, setPosts] = useState<BlogMeta[]>([]);
  const [currentPost, setCurrentPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  // Load single post
  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setError(null);

    const file = BLOG_FILES.find((f) => fileToSlug(f) === slug);
    if (!file) {
      setError("Post not found.");
      setLoading(false);
      return;
    }

    const base = (import.meta.env.BASE_URL ?? "/").replace(/\/$/, "") || "";
    fetch(`${base}/blog/${file}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load post");
        return r.text();
      })
      .then((raw) => {
        const { meta, body } = parseFrontmatter(raw);
        setCurrentPost({
          slug,
          ...meta,
          readTime: estimateReadTime(body),
          content: body,
        });
      })
      .catch(() => setError("Failed to load post."))
      .finally(() => setLoading(false));
  }, [slug]);

  // Load all post metadata for the list
  useEffect(() => {
    if (slug) return;
    setLoading(true);
    setError(null);

    const base = (import.meta.env.BASE_URL ?? "/").replace(/\/$/, "") || "";
    Promise.all(
      BLOG_FILES.map(async (file) => {
        const resp = await fetch(`${base}/blog/${file}`);
        if (!resp.ok) return null;
        const raw = await resp.text();
        const { meta, body } = parseFrontmatter(raw);
        return {
          slug: fileToSlug(file),
          ...meta,
          readTime: estimateReadTime(body),
        } as BlogMeta;
      }),
    )
      .then((results) => setPosts(results.filter(Boolean) as BlogMeta[]))
      .catch(() => setError("Failed to load blog posts."))
      .finally(() => setLoading(false));
  }, [slug]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        background: "var(--bg)",
      }}
    >
      <Nav
        projectName={config.projectName}
        lang={lang}
        theme={theme}
        onThemeToggle={onThemeToggle}
        docsPath="/docs"
        repoUrl={config.repoUrl}
        consoleUrl={config.consoleUrl}
      />

      <main
        style={{
          flex: 1,
          padding: "calc(var(--space-5) + 64px) var(--space-4) var(--space-5)",
          maxWidth: "var(--container)",
          margin: "0 auto",
          width: "100%",
        }}
      >
        {loading && (
          <div
            style={{
              textAlign: "center",
              padding: "var(--space-5)",
              color: "var(--text-muted)",
            }}
          >
            Loading...
          </div>
        )}

        {error && (
          <div
            style={{
              textAlign: "center",
              padding: "var(--space-5)",
              color: "var(--text-muted)",
            }}
          >
            <p>{error}</p>
            <Link
              to="/blog"
              style={{ color: "var(--accent)", textDecoration: "none" }}
            >
              Back to blog
            </Link>
          </div>
        )}

        {!loading && !error && !slug && <BlogList posts={posts} />}

        {!loading && !error && slug && currentPost && (
          <BlogPostView post={currentPost} />
        )}
      </main>

      <Footer lang={lang} />

      <style>{`
        .blog-card:hover {
          border-color: var(--accent) !important;
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        }
        .blog-back-link:hover {
          opacity: 0.8;
        }
        .blog-content h1,
        .blog-content h2,
        .blog-content h3 {
          color: var(--text);
          margin-top: 2rem;
          margin-bottom: 0.75rem;
        }
        .blog-content h2 { font-size: 1.5rem; }
        .blog-content h3 { font-size: 1.25rem; }
        .blog-content p {
          color: var(--text-muted);
          line-height: 1.7;
          margin-bottom: 1rem;
        }
        .blog-content a {
          color: var(--accent);
          text-decoration: none;
        }
        .blog-content a:hover {
          text-decoration: underline;
        }
        .blog-content ul, .blog-content ol {
          color: var(--text-muted);
          line-height: 1.7;
          padding-left: 1.5rem;
          margin-bottom: 1rem;
        }
        .blog-content li {
          margin-bottom: 0.375rem;
        }
        .blog-content code {
          background: var(--surface);
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
          font-size: 0.8125rem;
        }
        .blog-content pre {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 0.5rem;
          padding: 1rem;
          overflow-x: auto;
          margin-bottom: 1rem;
        }
        .blog-content pre code {
          background: none;
          padding: 0;
        }
        .blog-content blockquote {
          border-left: 3px solid var(--accent);
          padding-left: 1rem;
          color: var(--text-muted);
          font-style: italic;
          margin: 1rem 0;
        }
        .blog-content table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 1rem;
        }
        .blog-content th, .blog-content td {
          border: 1px solid var(--border);
          padding: 0.5rem 0.75rem;
          text-align: left;
          font-size: 0.875rem;
        }
        .blog-content th {
          background: var(--surface);
          color: var(--text);
          font-weight: 600;
        }
        .blog-content td {
          color: var(--text-muted);
        }
        .blog-content strong {
          color: var(--text);
        }
        .blog-content img {
          max-width: 100%;
          border-radius: 0.5rem;
        }
        .blog-content hr {
          border: none;
          border-top: 1px solid var(--border);
          margin: 2rem 0;
        }
      `}</style>
    </div>
  );
}
