'use client';
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { apiClient } from "@/lib/api"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/store"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CheckCircle2, AlertCircle, Brain, Shield, Zap, MessageSquare, Database, UserPlus } from "lucide-react"

export default function AuthPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login')
  const router = useRouter()
  const login = useAuthStore((state: any) => state.login)

  useEffect(() => {
    const stored = window.localStorage.getItem('theme');
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const nextTheme = stored === 'light' || stored === 'dark' ? stored : preferred;
    document.documentElement.classList.toggle('dark', nextTheme === 'dark');
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)
    const formData = new FormData(e.target as HTMLFormElement)
    const email = formData.get("email") as string
    const password = formData.get("password") as string

    try {
      const user = await apiClient.login(email, password)
      login(user)
      setSuccess("Login successful! Redirecting...")
      setTimeout(() => router.push("/"), 1000)
    } catch (error: any) {
      const errorMessage = error.message || "Login failed. Please check your credentials."
      
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
      const user = await apiClient.login(email, password)
      login(user)
      setTimeout(() => router.push("/"), 1000)
    } catch (error: any) {
      setError(error.message || "Registration failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-background text-foreground relative overflow-hidden py-10">
      {/* Brand - Top Right Corner */}
      <div className="absolute top-4 right-4 lg:top-6 lg:right-8 z-50 flex items-center space-x-2 lg:space-x-3">
        <div className="h-10 w-10 lg:h-14 lg:w-14 rounded-2xl logo-mark flex items-center justify-center shadow-2xl ring-2 ring-foreground/10 pulse-glow">
          <span className="text-primary-foreground font-black text-sm lg:text-lg tracking-[0.2em]">NX</span>
        </div>
        <div className="flex flex-col">
          <h1 className="text-2xl lg:text-4xl font-black tracking-tight text-foreground">
            NexusMind
          </h1>
          <span className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Studio RAG</span>
        </div>
      </div>

      {/* Aurora Background */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute inset-0 app-aurora" />
        <div className="absolute inset-0 bg-grid-soft opacity-60" />
        <div className="absolute inset-0 bg-noise opacity-40" />
      </div>

      <div className="w-full max-w-[1800px] grid lg:grid-cols-12 gap-6 lg:gap-12 items-start px-4 lg:px-8 relative z-10">
        
        {/* Left Side - Features & Branding */}
        <motion.div
          className="lg:col-span-7 space-y-6 text-foreground py-4"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          <div className="space-y-6">
            <div className="inline-flex items-center space-x-3 px-5 py-2.5 bg-accent-soft rounded-full border border-border/60 backdrop-blur-sm mb-2 shadow-lg">
              <Brain className="h-5 w-5 text-foreground" />
              <span className="text-sm font-semibold text-foreground">Next-Gen RAG Architecture</span>
            </div>
            
            <h1 className="text-5xl lg:text-8xl font-black tracking-tight leading-[1.1]">
              <span className="block text-foreground">
                Enterprise
              </span>
              <span className="block text-accent">
                Intelligence
              </span>
              <span className="block text-muted-foreground">
                Without Limits.
              </span>
            </h1>
            
            <p className="text-muted-foreground text-xl max-w-2xl leading-relaxed font-light">
              Experience the future of document analysis. Our professional-grade system combines hybrid search, intelligent reranking, and confidence scoring to deliver precise, context-aware answers from your data.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <div className="px-4 py-2 bg-muted/70 border border-border/60 rounded-full text-sm font-medium text-foreground backdrop-blur-sm whitespace-nowrap">
                🚀 LlamaIndex
              </div>
              <div className="px-4 py-2 bg-muted/70 border border-border/60 rounded-full text-sm font-medium text-foreground backdrop-blur-sm whitespace-nowrap">
                ⚡ Groq
              </div>
              <div className="px-4 py-2 bg-muted/70 border border-border/60 rounded-full text-sm font-medium text-foreground backdrop-blur-sm whitespace-nowrap">
                🔒 pgvector
              </div>
              <div className="px-4 py-2 bg-muted/70 border border-border/60 rounded-full text-sm font-medium text-foreground backdrop-blur-sm whitespace-nowrap">
                🤖 Ollama
              </div>
              <div className="px-4 py-2 bg-muted/70 border border-border/60 rounded-full text-sm font-medium text-foreground backdrop-blur-sm whitespace-nowrap">
                🎯 Reranker
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-foreground mb-4">Core Capabilities</h2>
            
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="relative bg-card/70 border border-border/70 p-6 rounded-2xl hover:border-foreground/20 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-muted/60 rounded-full blur-2xl group-hover:bg-muted/80 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-muted/60 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Zap className="h-7 w-7 text-foreground" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-foreground mb-2">Hybrid Search</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Combines BM25 keyword precision with semantic vector retrieval for unmatched accuracy. Get the best of both worlds.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-card/70 border border-border/70 p-6 rounded-2xl hover:border-foreground/20 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-muted/60 rounded-full blur-2xl group-hover:bg-muted/80 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-muted/60 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Database className="h-7 w-7 text-foreground" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-foreground mb-2">Smart Reranking</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Advanced BGE-reranker-v2-m3 model intelligently reorders results to ensure optimal context quality.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-card/70 border border-border/70 p-6 rounded-2xl hover:border-foreground/20 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-muted/60 rounded-full blur-2xl group-hover:bg-muted/80 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-muted/60 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Shield className="h-7 w-7 text-foreground" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-foreground mb-2">Confidence Scoring</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Multi-factor assessment evaluates retrieval quality, coherence, and coverage for guaranteed reliability.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-card/70 border border-border/70 p-6 rounded-2xl hover:border-foreground/20 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-muted/60 rounded-full blur-2xl group-hover:bg-muted/80 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-muted/60 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <MessageSquare className="h-7 w-7 text-foreground" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-foreground mb-2">Context Aware</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Maintains full conversational history enabling seamless follow-ups and deep contextual analysis.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-border/60 mt-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-4">
                <div className="h-14 w-14 rounded-full logo-mark flex items-center justify-center font-black text-primary-foreground text-xl shadow-xl ring-4 ring-foreground/10">
                  NX
                </div>
                <div>
                  <div className="font-bold text-foreground text-lg">Shivam Sourav</div>
                  <div className="text-sm text-muted-foreground font-medium">SDE at Nomura Fintech, Kolkata</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-1">Powered by</div>
                <div className="text-sm font-bold text-accent">
                  LlamaIndex & Groq
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Right Side - Auth Form */}
        <motion.div
          className="lg:col-span-5 w-full max-w-lg mx-auto lg:mr-0 flex items-center min-h-[calc(100vh-4rem)]"
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: 'easeOut', delay: 0.05 }}
        >
          <div className="relative glass-panel p-10 rounded-3xl overflow-hidden w-full">
            {/* Decorative Elements */}
            <div className="absolute top-0 left-0 w-full h-1 bg-accent-soft" />
            <div className="absolute -top-20 -right-20 w-64 h-64 bg-[radial-gradient(circle,rgba(124,124,255,0.2),transparent_70%)] rounded-full blur-3xl"></div>
            <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-[radial-gradient(circle,rgba(34,211,238,0.2),transparent_70%)] rounded-full blur-3xl"></div>
            
            <div className="flex flex-col space-y-3 text-center mb-10 relative z-10">
              <h2 className="text-4xl font-black tracking-tight text-accent">
                Welcome Back
              </h2>
              <p className="text-base text-muted-foreground">
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
            
            <div className="mt-10 text-center relative z-10">
              <p className="text-xs text-muted-foreground leading-relaxed">
                By continuing, you agree to our{" "}
                <a href="#" className="underline underline-offset-4 hover:text-blue-400 transition-colors font-medium">Terms of Service</a>
                {" "}and{" "}
                <a href="#" className="underline underline-offset-4 hover:text-blue-400 transition-colors font-medium">Privacy Policy</a>
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

