import UploadForm from '@/components/UploadForm'

export default function HomePage() {
  return (
    <section className="flex flex-1 flex-col justify-center">
      <div className="mx-auto w-full max-w-2xl rounded-3xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl shadow-blue-500/10">
        <UploadForm />
      </div>
    </section>
  )
}
