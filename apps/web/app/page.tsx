import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <h1 className="text-4xl font-bold text-indigo-600">ChatOpsLLM</h1>
      <p className="max-w-lg text-center text-slate-600">
        Production-grade LLMOps platform powered by FastAPI, LiteLLM, Celery, Qdrant, and Redis.
      </p>
      <Link
        href="/chat"
        className="rounded-xl bg-indigo-600 px-8 py-3 text-white font-semibold hover:bg-indigo-700 transition-colors"
      >
        Start Chatting
      </Link>
      <p className="text-xs text-slate-400">
        Built by Trần Quý Đạt · tranquydat.work@gmail.com
      </p>
    </main>
  );
}
