'use client';
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useState } from "react"
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
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 relative overflow-hidden py-8">
      {/* Logo & Brand - Top Right Corner - Responsive */}
      <div className="absolute top-4 right-4 lg:top-6 lg:right-8 z-50 flex items-center space-x-2 lg:space-x-3">
        <div className="h-10 w-10 lg:h-14 lg:w-14 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-2xl shadow-purple-900/50 ring-2 ring-white/20">
          <Brain className="h-6 w-6 lg:h-8 lg:w-8 text-white" />
        </div>
        <h1 className="text-2xl lg:text-4xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 drop-shadow-2xl">
          NexusMind RAG
        </h1>
      </div>

      {/* Ambient Background Effects */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[70%] h-[70%] rounded-full bg-blue-600/20 blur-[120px] animate-pulse" />
        <div className="absolute top-[40%] -right-[10%] w-[60%] h-[60%] rounded-full bg-purple-600/20 blur-[120px] animate-pulse" style={{animationDelay: '1s'}} />
        <div className="absolute bottom-[-10%] left-[20%] w-[50%] h-[50%] rounded-full bg-indigo-600/15 blur-[100px] animate-pulse" style={{animationDelay: '2s'}} />
        
        {/* Grid Pattern Overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:64px_64px]"></div>
      </div>

      <div className="w-full max-w-[1800px] grid lg:grid-cols-12 gap-6 lg:gap-12 items-start px-4 lg:px-8 relative z-10">
        
        {/* Left Side - Features & Branding */}
        <div className="lg:col-span-7 space-y-6 text-white py-4">
          <div className="space-y-6">
            <div className="inline-flex items-center space-x-3 px-5 py-2.5 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-full border border-blue-500/30 backdrop-blur-sm mb-2 shadow-lg shadow-blue-900/20">
              <Brain className="h-5 w-5 text-blue-400" />
              <span className="text-sm font-semibold text-zinc-100">Next-Gen RAG Architecture</span>
            </div>
            
            <h1 className="text-5xl lg:text-8xl font-black tracking-tight leading-[1.1]">
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-white via-zinc-100 to-zinc-300 drop-shadow-2xl">
                Enterprise
              </span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 drop-shadow-2xl">
                Intelligence
              </span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 drop-shadow-2xl">
                Without Limits.
              </span>
            </h1>
            
            <p className="text-zinc-300 text-xl max-w-2xl leading-relaxed font-light">
              Experience the future of document analysis. Our professional-grade system combines hybrid search, intelligent reranking, and confidence scoring to deliver precise, context-aware answers from your data.
            </p>

            <div className="flex flex-wrap gap-3 pt-2">
              <div className="px-4 py-2 bg-blue-600/10 border border-blue-500/20 rounded-full text-sm font-medium text-blue-300 backdrop-blur-sm whitespace-nowrap">
                🚀 LlamaIndex
              </div>
              <div className="px-4 py-2 bg-purple-600/10 border border-purple-500/20 rounded-full text-sm font-medium text-purple-300 backdrop-blur-sm whitespace-nowrap">
                ⚡ Groq
              </div>
              <div className="px-4 py-2 bg-green-600/10 border border-green-500/20 rounded-full text-sm font-medium text-green-300 backdrop-blur-sm whitespace-nowrap">
                🔒 pgvector
              </div>
              <div className="px-4 py-2 bg-orange-600/10 border border-orange-500/20 rounded-full text-sm font-medium text-orange-300 backdrop-blur-sm whitespace-nowrap">
                🤖 Ollama
              </div>
              <div className="px-4 py-2 bg-pink-600/10 border border-pink-500/20 rounded-full text-sm font-medium text-pink-300 backdrop-blur-sm whitespace-nowrap">
                🎯 Reranker
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-4">Core Capabilities</h2>
            
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="relative bg-gradient-to-br from-blue-900/30 to-blue-950/30 border border-blue-500/30 p-6 rounded-2xl hover:border-blue-400/50 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg hover:shadow-blue-900/30">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-blue-600/20 rounded-full blur-2xl group-hover:bg-blue-500/30 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-blue-500/30 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Zap className="h-7 w-7 text-blue-300" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-white mb-2">Hybrid Search</h3>
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      Combines BM25 keyword precision with semantic vector retrieval for unmatched accuracy. Get the best of both worlds.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-gradient-to-br from-purple-900/30 to-purple-950/30 border border-purple-500/30 p-6 rounded-2xl hover:border-purple-400/50 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg hover:shadow-purple-900/30">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-purple-600/20 rounded-full blur-2xl group-hover:bg-purple-500/30 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-purple-500/30 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Database className="h-7 w-7 text-purple-300" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-white mb-2">Smart Reranking</h3>
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      Advanced BGE-reranker-v2-m3 model intelligently reorders results to ensure optimal context quality.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-gradient-to-br from-green-900/30 to-green-950/30 border border-green-500/30 p-6 rounded-2xl hover:border-green-400/50 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg hover:shadow-green-900/30">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-green-600/20 rounded-full blur-2xl group-hover:bg-green-500/30 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-green-500/30 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Shield className="h-7 w-7 text-green-300" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-white mb-2">Confidence Scoring</h3>
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      Multi-factor assessment evaluates retrieval quality, coherence, and coverage for guaranteed reliability.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-gradient-to-br from-orange-900/30 to-orange-950/30 border border-orange-500/30 p-6 rounded-2xl hover:border-orange-400/50 transition-all duration-300 backdrop-blur-md group cursor-default shadow-lg hover:shadow-orange-900/30">
                <div className="absolute -top-2 -right-2 w-20 h-20 bg-orange-600/20 rounded-full blur-2xl group-hover:bg-orange-500/30 transition-all"></div>
                <div className="flex items-start space-x-4 relative z-10">
                  <div className="p-3 bg-orange-500/30 rounded-xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <MessageSquare className="h-7 w-7 text-orange-300" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-white mb-2">Context Aware</h3>
                    <p className="text-sm text-zinc-300 leading-relaxed">
                      Maintains full conversational history enabling seamless follow-ups and deep contextual analysis.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-white/10 mt-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center space-x-4">
                <div className="h-14 w-14 rounded-full bg-gradient-to-tr from-blue-600 via-purple-600 to-pink-600 flex items-center justify-center font-black text-white text-xl shadow-xl shadow-blue-900/30 ring-4 ring-white/10">
                  SS
                </div>
                <div>
                  <div className="font-bold text-white text-lg">Shivam Sourav</div>
                  <div className="text-sm text-blue-400 font-medium">SDE at Nomura Fintech, Kolkata</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-zinc-500 mb-1">Powered by</div>
                <div className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                  LlamaIndex & Groq
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side - Auth Form */}
        <div className="lg:col-span-5 w-full max-w-lg mx-auto lg:mr-0 flex items-center min-h-[calc(100vh-4rem)]">
          <div className="relative bg-gradient-to-br from-zinc-900/95 via-zinc-900/90 to-zinc-950/95 backdrop-blur-2xl p-10 rounded-3xl shadow-2xl border border-white/20 overflow-hidden w-full">
            {/* Decorative Elements */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />
            <div className="absolute -top-20 -right-20 w-64 h-64 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-full blur-3xl"></div>
            <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-gradient-to-tr from-purple-600/20 to-pink-600/20 rounded-full blur-3xl"></div>
            
            <div className="flex flex-col space-y-3 text-center mb-10 relative z-10">
              <h2 className="text-4xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-blue-100 to-purple-100">
                Welcome Back
              </h2>
              <p className="text-base text-zinc-400">
                Sign in to access your intelligent workspace
              </p>
            </div>

            <div className="relative z-10">
              <div className="flex w-full mb-10 p-1.5 bg-zinc-950/70 rounded-xl border border-white/10 shadow-inner">
                <button 
                  onClick={() => setActiveTab('login')}
                  className={`flex-1 rounded-lg transition-all duration-300 font-semibold py-3.5 ${
                    activeTab === 'login' 
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  Login
                </button>
                <button 
                  onClick={() => setActiveTab('register')}
                  className={`flex-1 rounded-lg transition-all duration-300 font-semibold py-3.5 ${
                    activeTab === 'register' 
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                      : 'text-zinc-400 hover:text-zinc-200'
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
                <Alert variant="destructive" className="mb-6 border-red-500/30 bg-red-500/10 text-red-200 backdrop-blur-sm animate-in fade-in-50 slide-in-from-top-5">
                  {error.toLowerCase().includes('redirecting') ? (
                    <UserPlus className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              {success && (
                <Alert className="mb-6 border-green-500/30 bg-green-500/10 text-green-200 backdrop-blur-sm animate-in fade-in-50 slide-in-from-top-5">
                  <CheckCircle2 className="h-4 w-4 text-green-400" />
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
              )}

              <TabsContent value="login" className="mt-0">
                <form onSubmit={handleLogin} className="space-y-6">
                  <div className="space-y-3">
                    <Label htmlFor="email" className="text-zinc-200 font-semibold text-sm">Email Address</Label>
                    <div className="relative group">
                      <Input 
                        id="email" 
                        name="email" 
                        type="email" 
                        placeholder="name@company.com" 
                        required 
                        className="h-14 bg-zinc-800/60 border-white/20 text-white placeholder:text-zinc-500 focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 transition-all rounded-xl text-base shadow-lg group-hover:border-white/30 [&:-webkit-autofill]:bg-zinc-800/60 [&:-webkit-autofill]:text-white [&:-webkit-autofill]:[-webkit-text-fill-color:white]" 
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="password" className="text-zinc-200 font-semibold text-sm">Password</Label>
                    <div className="relative group">
                      <Input 
                        id="password" 
                        name="password" 
                        type="password" 
                        required 
                        className="h-14 bg-zinc-800/60 border-white/20 text-white focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 transition-all rounded-xl text-base shadow-lg group-hover:border-white/30 [&:-webkit-autofill]:bg-zinc-800/60 [&:-webkit-autofill]:text-white" 
                      />
                    </div>
                  </div>
                  <Button 
                    className="w-full h-14 text-base font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white shadow-xl shadow-blue-900/40 transition-all hover:scale-[1.03] hover:shadow-2xl border-0 rounded-xl mt-8 relative overflow-hidden group" 
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
                    <Label htmlFor="register-email" className="text-zinc-200 font-semibold text-sm">Email Address</Label>
                    <div className="relative group">
                      <Input 
                        id="register-email" 
                        name="email" 
                        type="email" 
                        placeholder="name@company.com" 
                        required 
                        className="h-14 bg-zinc-800/60 border-white/20 text-white placeholder:text-zinc-500 focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 transition-all rounded-xl text-base shadow-lg group-hover:border-white/30 [&:-webkit-autofill]:bg-zinc-800/60 [&:-webkit-autofill]:text-white [&:-webkit-autofill]:[-webkit-text-fill-color:white]" 
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="register-password" className="text-zinc-200 font-semibold text-sm">Password</Label>
                    <div className="relative group">
                      <Input 
                        id="register-password" 
                        name="password" 
                        type="password" 
                        required 
                        className="h-14 bg-zinc-800/60 border-white/20 text-white focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 transition-all rounded-xl text-base shadow-lg group-hover:border-white/30 [&:-webkit-autofill]:bg-zinc-800/60 [&:-webkit-autofill]:text-white" 
                      />
                    </div>
                  </div>
                  <div className="space-y-3">
                    <Label htmlFor="confirm-password" className="text-zinc-200 font-semibold text-sm">Confirm Password</Label>
                    <div className="relative group">
                      <Input 
                        id="confirm-password" 
                        name="confirm-password" 
                        type="password" 
                        required 
                        className="h-14 bg-zinc-800/60 border-white/20 text-white focus:ring-2 focus:ring-blue-500/60 focus:border-blue-500/60 transition-all rounded-xl text-base shadow-lg group-hover:border-white/30 [&:-webkit-autofill]:bg-zinc-800/60 [&:-webkit-autofill]:text-white" 
                      />
                    </div>
                  </div>
                  <Button 
                    className="w-full h-14 text-base font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white shadow-xl shadow-blue-900/40 transition-all hover:scale-[1.03] hover:shadow-2xl border-0 rounded-xl mt-6 relative overflow-hidden group" 
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
              <p className="text-xs text-zinc-500 leading-relaxed">
                By continuing, you agree to our{" "}
                <a href="#" className="underline underline-offset-4 hover:text-blue-400 transition-colors font-medium">Terms of Service</a>
                {" "}and{" "}
                <a href="#" className="underline underline-offset-4 hover:text-blue-400 transition-colors font-medium">Privacy Policy</a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

