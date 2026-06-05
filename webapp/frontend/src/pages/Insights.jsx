import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function Insights() {
  const [markdown, setMarkdown] = useState("");

  useEffect(() => {
    fetch("/api/insights")
      .then((r) => r.json())
      .then((data) => setMarkdown(data.markdown))
      .catch(() => setMarkdown("_Failed to load insights._"));
  }, []);

  return (
    <div className="page markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  );
}
