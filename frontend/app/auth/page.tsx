'use client';
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { apiClient } from "@/lib/api"
import { useRouter } from "next/navigation"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CheckCircle2, AlertCircle, Brain, Shield, Zap, MessageSquare, Database, UserPlus, Sparkles, Radar, LineChart, FileSearch, Sun, Moon } from "lucide-react"

export default function AuthPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const router = useRouter()

  const inlineSvgs = {
    groq: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width="14" height="14"><g clip-path="url(#a)"><path fill="currentColor" d="M46.596 60.752H17L65.572 0 53.313 39.248h29.59L34.338 100z"/></g><defs><clipPath id="a"><path fill="#fff" d="M0 0h100v100H0z"/></clipPath></defs></svg>`,
    llamaindex: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width="14" height="14"><g clip-path="url(#a)"><path fill="url(#b)" d="M66.063 71.342c-8.717 3.85-18.159 2.27-21.792 1 0 .875-.042 3.57-.2 7.417-.158 3.85-1.383 6.279-1.98 7.016.067 2.404.121 7.654-.195 9.417A8.04 8.04 0 0 1 39.913 100h-5.35c.474-2.404 2.312-3.941 3.17-4.408.475-4.97-.458-9.288-.991-10.82-.525 1.87-1.821 6.207-2.771 8.616A26.7 26.7 0 0 1 31 98.8h-3.962c-.2-2.408 1.125-3.208 1.979-3.208.396-.738 1.346-3.046 1.983-6.417.633-3.362-.267-9.683-.792-12.42v-8.617c-6.341-3.409-8.716-6.817-10.304-10.625-1.267-3.042-.925-7.68-.591-9.617-.4-.733-1.555-2.604-1.984-5.208-.591-3.609-.262-6.213 0-7.617-.396-.4-1.187-2.446-1.187-7.417 0-4.966 1.454-7.545 2.179-8.216v-2.204c-2.775-.2-5.546-1.4-7.134-3.005-1.583-1.604-.395-4.008.596-4.808.992-.804 1.98-.204 3.367-.604s2.575-.8 3.167-2c.483-.97-.454-4.95-.984-6.817 2.375.321 3.896 2.404 4.359 3.409V0c2.97 1.404 8.32 4.809 10.104 12.225 1.425 5.934 2.441 18.371 2.77 23.846 7.596.067 17.238-1.083 25.955.804 7.92 1.717 11.487 5.209 15.646 5.209 4.162 0 6.541-2.405 9.508-.4 2.975 2.004 4.558 7.616 4.163 11.825-.317 3.366-2.905 4.475-4.159 4.608-1.583 5.292 0 10.354.988 12.225v7.612c.462.667 1.387 2.73 1.387 5.613 0 2.887-.925 4.808-1.387 5.412.791 4.488-.334 9.084-.992 10.821h-5.346c.634-1.604 1.717-2.004 2.18-2.004.95-4.97.262-9.554-.2-11.22-3.009-1.767-4.95-4.876-5.546-6.213.066 1.133-.121 4.287-1.388 7.812-1.267 3.53-3.167 5.613-3.958 6.213v4.208h-5.35c0-2.562 1.45-3.07 2.179-3.004.925-1.667 3.166-4.208 3.166-9.217 0-4.229-2.97-6.216-5.15-10.02-1.033-1.809-.529-4.076-.195-5.013z"/></g><defs><linearGradient id="b" x1="16.754" x2="102.554" y1="8.417" y2="80.321" gradientUnits="userSpaceOnUse"><stop offset=".062" stop-color="#f6dcd9"/><stop offset=".326" stop-color="#ffa5ea"/><stop offset=".589" stop-color="#45dff8"/><stop offset="1" stop-color="#bc8deb"/></linearGradient><clipPath id="a"><path fill="#fff" d="M0 0h100v100H0z"/></clipPath></defs></svg>`,
    cohere: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width="14" height="14"><path fill="#39594d" fill-rule="evenodd" d="M33.867 58.746c2.466 0 7.375-.138 14.158-2.93 7.904-3.254 23.633-9.166 34.98-15.233 7.937-4.241 11.416-9.858 11.416-17.416a19 19 0 0 0-19.004-19H31.454A27.29 27.29 0 0 0 4.167 31.458c0 15.071 11.437 27.288 29.7 27.288" clip-rule="evenodd"/><path fill="#d18ee2" fill-rule="evenodd" d="M41.3 77.541a18.28 18.28 0 0 1 11.27-16.883l13.847-5.75c14.004-5.809 29.416 4.483 29.416 19.646a21.267 21.267 0 0 1-21.27 21.266l-14.988-.004A18.276 18.276 0 0 1 41.3 77.537z" clip-rule="evenodd"/><path fill="#ff7759" d="M19.9 62.341A15.73 15.73 0 0 0 4.167 78.075v2.037a15.733 15.733 0 0 0 31.462 0V78.07A15.73 15.73 0 0 0 19.9 62.341"/></svg>`,
    copilot: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width="14" height="14"><g clip-path="url(#a)"><path fill="url(#b)" d="M73.055 12.558A10.52 10.52 0 0 0 62.96 5h-3.072a10.52 10.52 0 0 0-10.35 8.623l-5.261 28.669 1.305-4.467a10.52 10.52 0 0 1 10.101-7.57h17.85l7.487 2.915 7.216-2.916H86.13a10.52 10.52 0 0 1-10.096-7.557z"/><path fill="url(#c)" d="M28.026 88.315a10.52 10.52 0 0 0 10.109 7.6h6.524a10.52 10.52 0 0 0 10.519-10.252l.71-27.643-1.486 5.076a10.52 10.52 0 0 1-10.099 7.565H26.305l-6.417-3.481-6.947 3.482h2.072c4.685 0 8.807 3.098 10.108 7.6z"/><path fill="url(#d)" d="M62.503 5H26.047C15.631 5 9.383 18.766 5.216 32.532c-4.937 16.31-11.395 38.12 7.291 38.12h15.74c4.705 0 8.834-3.11 10.127-7.633 2.736-9.574 7.533-26.277 11.3-38.992 1.914-6.462 3.51-12.011 5.956-15.467C57.004 6.623 59.29 5 62.503 5"/><path fill="url(#e)" d="M62.503 5H26.047C15.631 5 9.383 18.766 5.216 32.532c-4.937 16.31-11.395 38.12 7.291 38.12h15.74c4.705 0 8.834-3.11 10.127-7.633 2.736-9.574 7.533-26.277 11.3-38.992 1.914-6.462 3.51-12.011 5.956-15.467C57.004 6.623 59.29 5 62.503 5"/><path fill="url(#f)" d="M37.497 95.915h36.457c10.415 0 16.664-13.768 20.831-27.536 4.936-16.312 11.394-38.127-7.291-38.127H71.752a10.525 10.525 0 0 0-10.126 7.633c-2.736 9.576-7.533 26.283-11.3 39-1.915 6.463-3.51 12.014-5.957 15.47-1.373 1.938-3.66 3.56-6.872 3.56"/><path fill="url(#g)" d="M37.497 95.915h36.457c10.415 0 16.664-13.768 20.831-27.536 4.936-16.312 11.394-38.127-7.291-38.127H71.752a10.525 10.525 0 0 0-10.126 7.633c-2.736 9.576-7.533 26.283-11.3 39-1.915 6.463-3.51 12.014-5.957 15.47-1.373 1.938-3.66 3.56-6.872 3.56"/></g><defs><radialGradient id="b" cx="0" cy="0" r="1" gradientTransform="rotate(230.696 50.992 1.884)scale(39.3283 36.9813)" gradientUnits="userSpaceOnUse"><stop offset=".096" stop-color="#00aeff"/><stop offset=".773" stop-color="#2253ce"/><stop offset="1" stop-color="#0736c4"/></radialGradient><radialGradient id="c" cx="0" cy="0" r="1" gradientTransform="rotate(51.84 -62.162 56.578)scale(36.346 35.2566)" gradientUnits="userSpaceOnUse"><stop stop-color="#ffb657"/><stop offset=".634" stop-color="#ff5f3d"/><stop offset=".923" stop-color="#c02b3c"/></radialGradient><radialGradient id="f" cx="0" cy="0" r="1" gradientTransform="rotate(109.274 36.23 43.622)scale(87.2497 104.523)" gradientUnits="userSpaceOnUse"><stop offset=".066" stop-color="#8c48ff"/><stop offset=".5" stop-color="#f2598a"/><stop offset=".896" stop-color="#ffb152"/></radialGradient><linearGradient id="d" x1="23.865" x2="29.067" y1="12.955" y2="73.13" gradientUnits="userSpaceOnUse"><stop offset=".156" stop-color="#0d91e1"/><stop offset=".487" stop-color="#52b471"/><stop offset=".652" stop-color="#98bd42"/><stop offset=".937" stop-color="#ffc800"/></linearGradient><linearGradient id="e" x1="28.411" x2="31.251" y1="5" y2="70.653" gradientUnits="userSpaceOnUse"><stop stop-color="#3dcbff"/><stop offset=".247" stop-color="#0588f7" stop-opacity="0"/></linearGradient><linearGradient id="g" x1="92.247" x2="92.209" y1="26.242" y2="44.127" gradientUnits="userSpaceOnUse"><stop offset=".058" stop-color="#f8adfa"/><stop offset=".708" stop-color="#a86edd" stop-opacity="0"/></linearGradient><clipPath id="a"><path fill="#fff" d="M0 0h100v100H0z"/></clipPath></defs></svg>`,
    uvicorn: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 100 100" width="14" height="14"><path fill="#fff" d="M29.883 84.434c-3.81-2.996-7.873-5.87-10.65-9.914C13.39 67.386 8.891 59.127 5.815 50.447 3.956 44.804 3.32 38.753.923 33.327c-2.507-3.941.43-8.249 4.747-9.501 1.921-.37 5.3-2.182 1.222-.887-3.657 2.684-4.011-2.435-.262-2.759 2.56-.34 3.502-2.435 2.626-4.321-2.746-1.792 6.662-3.76 1.928-6.433-4.932-5.32 6.898-6.345 3.98-.303-.7 4.647 8.266-.851 6.186 4.515 2.113 2.576 7.916.586 7.772 4.2 3.08.212 4.137 2.804 7.028 3.003 2.997 1.353 8.428 2.42 9.448 5.796-2.973 2.353-9.856-4.862-10.187 1.653.898 9.624.669 19.537 4.19 28.7 1.665 5.55 5.702 9.918 9.348 14.24 3.49 4.233 8.215 7.213 13.031 9.721 4.225 1.994 8.78 3.315 13.385 4.144 1.867-1.428 5.164-6.74 8.078-4.5.138 2.517-5.782 5.26-.279 4.982 3.232-.975 5.474 2.5 8.135-.635 2.452 2.905 10.192-1.855 8.447 4.082-2.359 1.522-5.8.602-8.162 2.696-3.896-1.946-6.998 1.741-11.312 1.275-4.79.858-9.662 1.204-14.519 1.212-7.967-.63-16.102-.895-23.682-3.67-4.268-1.24-8.436-3.671-12.188-6.103"/></svg>`,
    drawio: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none" width="14" height="14"><rect x="8" y="14" width="64" height="52" rx="8" stroke="#2b2b2b" stroke-width="6"/><path d="M24 70l40 12" stroke="#2b2b2b" stroke-width="6" stroke-linecap="round"/><path d="M52 26l18 18-28 8 10-26z" fill="#f59e0b"/></svg>`,
  }

  const stackLogos = [
    { name: 'LlamaIndex', inlineSvg: inlineSvgs.llamaindex },
    { name: 'Groq', inlineSvg: inlineSvgs.groq },
    { name: 'Cohere', inlineSvg: inlineSvgs.cohere },
    { name: 'Copilot', inlineSvg: inlineSvgs.copilot },
    { name: 'Ollama', slug: 'ollama' },
    { name: 'Lightning.ai', slug: 'lightning' },
    { name: 'Draw.io', inlineSvg: inlineSvgs.drawio },
    { name: 'PostgreSQL', slug: 'postgresql' },
    { name: 'pgvector', slug: 'postgresql' },
    { name: 'Python', slug: 'python' },
    { name: 'FastAPI', slug: 'fastapi' },
    { name: 'SQLAlchemy', slug: 'sqlalchemy' },
    { name: 'Pydantic', slug: 'pydantic' },
    { name: 'Uvicorn', inlineSvg: inlineSvgs.uvicorn },
    { name: 'Docker', slug: 'docker' },
    { name: 'Next.js', slug: 'nextdotjs' },
    { name: 'React', slug: 'react' },
    { name: 'Tailwind CSS', slug: 'tailwindcss' },
    { name: 'TypeScript', slug: 'typescript' },
  ].map((item) => ({
    name: item.name,
    inlineSvg: item.inlineSvg,
    sources: item.slug
      ? [
          `https://cdn.simpleicons.org/${item.slug}`,
          `https://simpleicons.org/icons/${item.slug}.svg`,
          `https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/${item.slug}.svg`,
          `https://api.iconify.design/simple-icons:${item.slug}.svg`,
        ]
      : [],
  }))

  const LogoBadge = ({
    name,
    sources,
    inlineSvg,
  }: {
    name: string
    sources: string[]
    inlineSvg?: string
  }) => {
    const [srcIndex, setSrcIndex] = useState(0)
    const [hidden, setHidden] = useState(false)
    const src = sources[srcIndex]

    const handleError = () => {
      if (srcIndex + 1 < sources.length) {
        setSrcIndex((current) => current + 1)
        return
      }
      setHidden(true)
    }

    return (
      <div className="flex w-[190px] items-center justify-center gap-2 rounded-full border border-border/60 bg-muted/60 px-4 py-1.5 text-[11px] font-medium text-muted-foreground whitespace-nowrap">
        {inlineSvg ? (
          <span
            className="h-3.5 w-3.5 text-foreground/70"
            aria-hidden="true"
            dangerouslySetInnerHTML={{ __html: inlineSvg }}
          />
        ) : !hidden && src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={src}
            alt=""
            className="h-3.5 w-3.5 opacity-80"
            onError={handleError}
          />
        ) : null}
        {name}
      </div>
    )
  }

  useEffect(() => {
    if (typeof window === 'undefined') return
    const stored = window.localStorage.getItem('theme')
    if (stored === 'light' || stored === 'dark') {
      setTheme(stored)
    }
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    document.documentElement.classList.toggle('dark', theme === 'dark')
    window.localStorage.setItem('theme', theme)
  }, [theme])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)
    const formData = new FormData(e.target as HTMLFormElement)
    const email = formData.get("email") as string
    const password = formData.get("password") as string

    try {
      await apiClient.login(email, password)
      setSuccess("Login successful! Redirecting...")
      setTimeout(() => router.push("/"), 1000)
    } catch (error: unknown) {
      const errorMessage = error instanceof Error
        ? error.message
        : "Login failed. Please check your credentials."
      
      // Check if user not found (400 status or specific error message)
      if (errorMessage.toLowerCase().includes('user not found') || 
          errorMessage.toLowerCase().includes('not found') ||
          errorMessage.toLowerCase().includes('does not exist') ||
          errorMessage.toLowerCase().includes('no user') ||
          errorMessage.toLowerCase().includes('invalid email')) {
        
        // Show special message for user not found
        setError("Account not found! Redirecting you to registration...")
        
        // Redirect to register tab after 2 seconds
        setTimeout(() => {
          setActiveTab('register')
          setError(null)
          setSuccess("Please create a new account to continue")
        }, 2000)
      } else {
        setError(errorMessage)
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)
    const formData = new FormData(e.target as HTMLFormElement)
    const email = formData.get("email") as string
    const password = formData.get("password") as string
    const confirmPassword = formData.get("confirm-password") as string

    if (password !== confirmPassword) {
      setError("Passwords do not match")
      setIsLoading(false)
      return
    }

    try {
      await apiClient.register(email, password)
      setSuccess("Account created successfully! Logging you in...")
      // Auto login after register
      await apiClient.login(email, password)
      setTimeout(() => router.push("/"), 1000)
    } catch (error: unknown) {
      const errorMessage = error instanceof Error
        ? error.message
        : "Registration failed. Please try again."
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-background text-foreground relative overflow-x-hidden flex flex-col">
      {/* Brand - Top Right Corner */}
      <div className="absolute top-4 right-4 lg:top-6 lg:right-8 z-50 flex items-center space-x-2 lg:space-x-3">
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <div className="h-10 w-10 lg:h-12 lg:w-12 rounded-2xl logo-mark flex items-center justify-center shadow-2xl ring-1 ring-black/10 dark:ring-white/5 pulse-glow">
          <span className="text-primary-foreground font-black text-sm tracking-[0.2em]">NX</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-xl lg:text-2xl font-black tracking-tight text-foreground">
            NexusMind
          </h1>
          <span className="text-[9px] uppercase tracking-[0.3em] text-muted-foreground">Studio RAG</span>
        </div>
      </div>

      {/* Aurora Background */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute inset-0 app-aurora" />
        <div className="absolute inset-0 bg-grid-soft opacity-40" />
        <div className="absolute inset-0 bg-noise opacity-30" />
        <div className="absolute -top-32 right-[-10%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.14),transparent_65%)] blur-3xl float-slow" />
        <div className="absolute top-[15%] left-[-8%] h-[380px] w-[380px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.16),transparent_65%)] blur-3xl float-slower" />
      </div>

      <div className="w-full max-w-[1800px] mx-auto grid lg:grid-cols-12 gap-6 lg:gap-10 items-center px-4 lg:px-8 relative z-10 flex-1 py-8 min-h-screen">
        
        {/* Left Side - Features & Branding */}
        <motion.div
          className="lg:col-span-7 space-y-6 text-foreground py-4"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <div className="space-y-5">
            <div className="inline-flex items-center space-x-3 px-4 py-2 rounded-full border border-[hsl(var(--chart-2)/0.35)] bg-[hsl(var(--chart-2)/0.14)] backdrop-blur-sm shadow-md">
              <Brain className="h-4 w-4 text-foreground" />
              <span className="text-xs font-semibold text-foreground tracking-wide">Unified AI Workspace</span>
            </div>
            
            <h1 className="text-4xl lg:text-7xl font-black tracking-tight leading-[1.08]">
              <span className="block text-foreground">
                Enterprise
              </span>
              <span className="block text-accent">
                Intelligence
              </span>
              <span className="block text-muted-foreground/80 text-3xl lg:text-5xl mt-1">
                Without Limits.
              </span>
            </h1>
            
            <p className="text-muted-foreground text-base lg:text-lg max-w-xl leading-relaxed">
              End-to-end AI workspace for RAG chat, AuraSQL analytics, Nexus resume scoring, and ResumeGen PDF creation with traceable outputs.
            </p>

            <div className="flex flex-wrap gap-2 pt-1">
              {[
                { icon: Sparkles, label: 'RAG Chat', tone: 'border-[hsl(var(--chart-1)/0.34)] bg-[hsl(var(--chart-1)/0.12)]' },
                { icon: Database, label: 'AuraSQL', tone: 'border-[hsl(var(--chart-2)/0.34)] bg-[hsl(var(--chart-2)/0.12)]' },
                { icon: Radar, label: 'Nexus Scoring', tone: 'border-[hsl(var(--chart-4)/0.34)] bg-[hsl(var(--chart-4)/0.12)]' },
                { icon: FileSearch, label: 'ResumeGen PDF', tone: 'border-[hsl(var(--chart-5)/0.34)] bg-[hsl(var(--chart-5)/0.12)]' },
                { icon: LineChart, label: 'Traceability', tone: 'border-[hsl(var(--foreground)/0.18)] bg-[hsl(var(--foreground)/0.06)]' },
              ].map(({ icon: Icon, label, tone }) => (
                <div key={label} className={`px-3 py-1.5 border rounded-full text-xs font-medium text-foreground/85 backdrop-blur-sm inline-flex items-center gap-1.5 ${tone}`}>
                  <Icon className="h-3 w-3" />
                  {label}
                </div>
              ))}
            </div>
          </div>

          {/* Compact feature cards */}
          <div className="grid sm:grid-cols-2 gap-3 pt-2">
            {[
              {
                icon: MessageSquare,
                title: 'RAG Chat',
                desc: 'Hybrid retrieval with reasoning modes, source traces, and confidence-aware responses.',
                cardTone: 'border-[hsl(var(--chart-1)/0.34)] bg-[hsl(var(--chart-1)/0.10)]',
                iconTone: 'bg-[hsl(var(--chart-1)/0.18)]',
              },
              {
                icon: Database,
                title: 'AuraSQL',
                desc: 'Natural language to SQL with schema context, confidence metadata, and query history.',
                cardTone: 'border-[hsl(var(--chart-2)/0.34)] bg-[hsl(var(--chart-2)/0.10)]',
                iconTone: 'bg-[hsl(var(--chart-2)/0.18)]',
              },
              {
                icon: Shield,
                title: 'Nexus Resume',
                desc: 'Resume upload, scoring, and JD matching workflow with persisted analysis history.',
                cardTone: 'border-[hsl(var(--chart-4)/0.34)] bg-[hsl(var(--chart-4)/0.10)]',
                iconTone: 'bg-[hsl(var(--chart-4)/0.18)]',
              },
              {
                icon: Zap,
                title: 'ResumeGen',
                desc: 'Structured resume builder with LaTeX/PDF generation ready for deployment workflows.',
                cardTone: 'border-[hsl(var(--chart-5)/0.34)] bg-[hsl(var(--chart-5)/0.10)]',
                iconTone: 'bg-[hsl(var(--chart-5)/0.18)]',
              },
            ].map(({ icon: Icon, title, desc, cardTone, iconTone }) => (
              <div key={title} className={`border p-4 rounded-2xl hover:border-foreground/20 transition-all backdrop-blur-sm group cursor-default ${cardTone}`}>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg group-hover:scale-105 transition-transform ${iconTone}`}>
                    <Icon className="h-5 w-5 text-foreground/80" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-foreground mb-1">{title}</h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4 border-t border-border/40 mt-4">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-3">
                <div className="h-11 w-11 rounded-full logo-mark flex items-center justify-center font-black text-primary-foreground text-base shadow-lg ring-1 ring-black/10 dark:ring-white/5">
                  NX
                </div>
                <div>
                  <div className="font-bold text-foreground text-sm">Shivam Sourav</div>
                  <div className="text-xs text-muted-foreground">SDE at Nomura Fintech, Kolkata</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-muted-foreground mb-0.5">Powered by</div>
                <div className="text-xs font-bold text-accent">LlamaIndex & Groq</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Right Side - Auth Form */}
        <motion.div
          className="lg:col-span-5 w-full max-w-md mx-auto lg:mr-0"
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: 'easeOut', delay: 0.05 }}
        >
          <div className="relative glass-panel p-8 rounded-3xl overflow-hidden w-full">
            {/* Decorative Elements */}
            <div className="absolute top-0 left-0 w-full h-0.5 bg-accent-soft" />
            <div className="absolute -top-20 -right-20 w-48 h-48 bg-[radial-gradient(circle,hsl(var(--chart-1)/0.15),transparent_70%)] rounded-full blur-3xl" />
            <div className="absolute -bottom-20 -left-20 w-48 h-48 bg-[radial-gradient(circle,hsl(var(--chart-2)/0.15),transparent_70%)] rounded-full blur-3xl" />
            
            <div className="flex flex-col space-y-2 text-center mb-8 relative z-10">
              <h2 className="text-3xl font-black tracking-tight text-accent">
                Welcome Back
              </h2>
              <p className="text-sm text-muted-foreground">
                Sign in to access your intelligent workspace
              </p>
            </div>

            <div className="relative z-10">
              <div className="flex w-full mb-10 p-1.5 bg-muted/70 rounded-xl border border-border/70 shadow-inner">
                <button 
                  onClick={() => setActiveTab('login')}
                  className={`flex-1 rounded-lg transition-all duration-300 font-semibold py-3.5 ${
                    activeTab === 'login' 
                      ? 'bg-foreground text-background shadow-lg' 
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Login
                </button>
                <button 
                  onClick={() => setActiveTab('register')}
                  className={`flex-1 rounded-lg transition-all duration-300 font-semibold py-3.5 ${
                    activeTab === 'register' 
                      ? 'bg-foreground text-background shadow-lg' 
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Register
                </button>
              </div>

              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'login' | 'register')} className="w-full">
                <TabsList className="hidden">
                  <TabsTrigger value="login">Login</TabsTrigger>
                  <TabsTrigger value="register">Register</TabsTrigger>
                </TabsList>
              
              {error && (
                <Alert variant="destructive" className="mb-6 border-red-500/30 bg-red-500/10 text-red-600 backdrop-blur-sm animate-in fade-in-50 slide-in-from-top-5">
                  {error.toLowerCase().includes('redirecting') ? (
                    <UserPlus className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              {success && (
                <Alert className="mb-6 border-emerald-500/30 bg-emerald-500/10 text-emerald-600 backdrop-blur-sm animate-in fade-in-50 slide-in-from-top-5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}

              <TabsContent value="login" className="mt-0">
                <form onSubmit={handleLogin} className="space-y-6">
                  <div className="space-y-3">
                    <Label htmlFor="email" className="text-foreground font-semibold text-sm">Email Address</Label>
                    <div className="relative group">
                      <Input 
                        id="email" 
                        name="email" 
                        type="email" 
                        placeholder="name@company.com" 
                        required 
                        className="h-14 bg-card/80 border-border/70 text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/40 focus:border-primary/40 transition-all rounded-xl text-base shadow-lg group-hover:border-border/90 [&:-webkit-autofill]:bg-card/80 [&:-webkit-autofill]:text-foreground [&:-webkit-autofill]:[-webkit-text-fill-color:inherit]" 
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="password" className="text-foreground font-semibold text-sm">Password</Label>
                    <div className="relative group">
                      <Input 
                        id="password" 
                        name="password" 
                        type="password" 
                        required 
                        className="h-14 bg-card/80 border-border/70 text-foreground focus:ring-2 focus:ring-primary/40 focus:border-primary/40 transition-all rounded-xl text-base shadow-lg group-hover:border-border/90 [&:-webkit-autofill]:bg-card/80 [&:-webkit-autofill]:text-foreground" 
                      />
                    </div>
                  </div>
                  <Button 
                    className="w-full h-14 text-base font-bold bg-foreground text-background hover:bg-foreground/90 shadow-xl transition-all hover:scale-[1.03] hover:shadow-2xl border-0 rounded-xl mt-8 relative overflow-hidden group" 
                    type="submit" 
                    disabled={isLoading}
                  >
                    <span className="relative z-10 flex items-center justify-center gap-2">
                      {isLoading ? "Authenticating..." : (
                        <>
                          Sign In to Dashboard
                          <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </>
                      )}
                    </span>
                    <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity blur-xl"></div>
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register" className="mt-0">
                <form onSubmit={handleRegister} className="space-y-5">
                  <div className="space-y-3">
                    <Label htmlFor="register-email" className="text-foreground font-semibold text-sm">Email Address</Label>
                    <div className="relative group">
                      <Input 
                        id="register-email" 
                        name="email" 
                        type="email" 
                        placeholder="name@company.com" 
                        required 
                        className="h-14 bg-card/80 border-border/70 text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/40 focus:border-primary/40 transition-all rounded-xl text-base shadow-lg group-hover:border-border/90 [&:-webkit-autofill]:bg-card/80 [&:-webkit-autofill]:text-foreground [&:-webkit-autofill]:[-webkit-text-fill-color:inherit]" 
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="register-password" className="text-foreground font-semibold text-sm">Password</Label>
                    <div className="relative group">
                      <Input 
                        id="register-password" 
                        name="password" 
                        type="password" 
                        required 
                        className="h-14 bg-card/80 border-border/70 text-foreground focus:ring-2 focus:ring-primary/40 focus:border-primary/40 transition-all rounded-xl text-base shadow-lg group-hover:border-border/90 [&:-webkit-autofill]:bg-card/80 [&:-webkit-autofill]:text-foreground" 
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="confirm-password" className="text-foreground font-semibold text-sm">Confirm Password</Label>
                    <div className="relative group">
                      <Input 
                        id="confirm-password" 
                        name="confirm-password" 
                        type="password" 
                        required 
                        className="h-14 bg-card/80 border-border/70 text-foreground focus:ring-2 focus:ring-primary/40 focus:border-primary/40 transition-all rounded-xl text-base shadow-lg group-hover:border-border/90 [&:-webkit-autofill]:bg-card/80 [&:-webkit-autofill]:text-foreground" 
                      />
                    </div>
                  </div>
                  <Button 
                    className="w-full h-14 text-base font-bold bg-foreground text-background hover:bg-foreground/90 shadow-xl transition-all hover:scale-[1.03] hover:shadow-2xl border-0 rounded-xl mt-6 relative overflow-hidden group" 
                    type="submit" 
                    disabled={isLoading}
                  >
                    <span className="relative z-10 flex items-center justify-center gap-2">
                      {isLoading ? "Creating Account..." : (
                        <>
                          Create Free Account
                          <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </>
                      )}
                    </span>
                    <div className="absolute inset-0 bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity blur-xl"></div>
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
            </div>
            
            <div className="mt-8 text-center relative z-10">
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                By continuing, you agree to our{" "}
                <a href="#" className="underline underline-offset-4 hover:text-blue-400 transition-colors font-medium">Terms</a>
                {" "}and{" "}
                <a href="#" className="underline underline-offset-4 hover:text-blue-400 transition-colors font-medium">Privacy Policy</a>
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Stack bar - fixed bottom */}
      <div className="fixed bottom-4 left-1/2 z-20 w-[min(1100px,92vw)] -translate-x-1/2 overflow-hidden">
        <div className="rounded-2xl border border-border/40 bg-background/70 backdrop-blur-xl px-4 py-3 shadow-[0_16px_48px_-40px_rgba(0,0,0,0.4)]">
          <div className="flex items-center justify-between mb-2">
            <div className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground">Stack</div>
            <div className="text-[10px] text-muted-foreground">Core providers</div>
          </div>
          <div className="overflow-hidden marquee">
            <div className="flex w-[200%] gap-3 marquee-track">
              {stackLogos.map((logo) => (
                <LogoBadge
                  key={`${logo.name}-1`}
                  name={logo.name}
                  sources={logo.sources}
                  inlineSvg={logo.inlineSvg}
                />
              ))}
              {stackLogos.map((logo) => (
                <LogoBadge
                  key={`${logo.name}-2`}
                  name={logo.name}
                  sources={logo.sources}
                  inlineSvg={logo.inlineSvg}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
