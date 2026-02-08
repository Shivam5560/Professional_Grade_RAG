'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Briefcase,
  Calendar,
  Cpu,
  GraduationCap,
  Github,
  Linkedin,
  Mail,
  MapPin,
  Phone,
  Sparkles,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

const skillGroups = [
  {
    title: 'Languages and Tools',
    items: ['Python', 'Java', 'R', 'C', 'C++', 'SQL', 'Git', 'GitHub', 'Jenkins', 'Spring Boot', 'Apache Tomcat', 'ActiveMQ'],
  },
  {
    title: 'Frameworks and Libraries',
    items: ['TensorFlow', 'PyTorch', 'Keras', 'Scikit-Learn', 'XGBoost', 'Prophet', 'Hugging Face', 'NLTK', 'LlamaIndex', 'Flask', 'Streamlit', 'Gradio', 'Camunda'],
  },
  {
    title: 'Data and Visualization',
    items: ['Pandas', 'NumPy', 'MongoDB', 'OracleDB', 'PostgreSQL', 'Power BI', 'Tableau', 'Looker', 'Plotly'],
  },
  {
    title: 'LLM and Retrieval',
    items: ['LlamaIndex', 'Cohere', 'Pinecone', 'Groq LLMs', 'OpenAI GPT-OSS 20B'],
  },
  {
    title: 'DevOps',
    items: ['Docker', 'Jenkins CI/CD', 'Micro-services architecture', 'Camunda workflow orchestration'],
  },
];

function AnimatedCounter({ value, suffix = '', duration = 1600 }: { value: number; suffix?: string; duration?: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * value));
      if (progress < 1) {
        frame = requestAnimationFrame(step);
      }
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return (
    <span>
      {display}
      {suffix}
    </span>
  );
}

export default function DeveloperPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-12">
        <div className="max-w-6xl mx-auto space-y-12">
          <section className="glass-panel rounded-[32px] p-6 md:p-10 relative overflow-hidden">
            <div className="absolute -top-24 -right-16 h-64 w-64 rounded-full bg-accent-soft blur-2xl float-slow" />
            <div className="absolute -bottom-20 left-4 h-56 w-56 rounded-full bg-accent-soft blur-2xl float-slower" />
            <div className="absolute inset-0 intro-sheen" />

            <div className="relative grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
              <div className="space-y-5">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge className="bg-foreground text-background">Developer Profile</Badge>
                  <Badge variant="outline" className="border-border/60">Shivam_AI.pdf</Badge>
                </div>
                <h1 className="text-4xl md:text-5xl font-black tracking-tight leading-tight">
                  Shivam <span className="text-accent">Sourav</span>
                </h1>
                <p className="text-muted-foreground text-base md:text-lg max-w-xl">
                  Software engineer building production-grade AI systems, hybrid retrieval pipelines, and workflow-driven platforms.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => router.push('/')}>Back to Dashboard</Button>
                  <Button variant="outline" asChild>
                    <a href="mailto:shivam99806@gmail.com">
                      <Mail className="h-4 w-4 mr-2" />
                      Email
                    </a>
                  </Button>
                </div>
                <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                  <span className="inline-flex items-center gap-2">
                    <MapPin className="h-4 w-4" />
                    Banka, Bihar, India
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <Phone className="h-4 w-4" />
                    +91 8521846844
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Education</p>
                  <div className="mt-3 space-y-2">
                    <p className="font-semibold text-foreground">B.Tech in Artificial Intelligence and Data Science</p>
                    <p className="text-sm text-muted-foreground">Sikkim Manipal Institute of Technology</p>
                    <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                      <span className="inline-flex items-center gap-2">
                        <GraduationCap className="h-4 w-4" />
                        Expected May 2025
                      </span>
                      <span className="inline-flex items-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        CGPA 9.7
                      </span>
                    </div>
                  </div>
                </div>
                <div className="rounded-3xl border border-border/60 bg-card/70 p-5 space-y-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Professional Links</p>
                  <div className="flex flex-wrap gap-3">
                    <Button variant="outline" asChild>
                      <a href="https://linkedin.com/in/shivam-sourav-b889aa204/" target="_blank" rel="noreferrer">
                        <Linkedin className="h-4 w-4 mr-2" />
                        LinkedIn
                      </a>
                    </Button>
                    <Button variant="outline" asChild>
                      <a href="https://github.com/Shivam5560" target="_blank" rel="noreferrer">
                        <Github className="h-4 w-4 mr-2" />
                        GitHub
                      </a>
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card className="glass-panel border-border/60 hover-glow">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Sparkles className="h-4 w-4 text-primary" />
                  <span className="text-3xl font-black tracking-tight">
                    <AnimatedCounter value={90} suffix="%+" />
                  </span>
                </CardTitle>
                <CardDescription>ATS resume matching accuracy.</CardDescription>
              </CardHeader>
            </Card>
            <Card className="glass-panel border-border/60 hover-glow">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Cpu className="h-4 w-4 text-primary" />
                  <span className="text-3xl font-black tracking-tight">
                    <AnimatedCounter value={95} suffix="%" />
                  </span>
                </CardTitle>
                <CardDescription>Flood prediction accuracy (92-95%).</CardDescription>
              </CardHeader>
            </Card>
            <Card className="glass-panel border-border/60 hover-glow">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Briefcase className="h-4 w-4 text-primary" />
                  <span className="text-3xl font-black tracking-tight">
                    <AnimatedCounter value={60} suffix="%" />
                  </span>
                </CardTitle>
                <CardDescription>Dev time reduction for scaffolding.</CardDescription>
              </CardHeader>
            </Card>
            <Card className="glass-panel border-border/60 hover-glow">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-primary" />
                  <span className="text-3xl font-black tracking-tight">
                    <AnimatedCounter value={60} suffix="%" />
                  </span>
                </CardTitle>
                <CardDescription>Faster OracleDB validation cycles.</CardDescription>
              </CardHeader>
            </Card>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <Card className="glass-panel border-border/60 hover-glow">
              <CardHeader>
                <CardTitle>Professional Experience</CardTitle>
                <CardDescription>Outcome-driven roles and platform impact.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 text-sm text-muted-foreground relative">
                <span className="absolute left-1.5 top-4 bottom-6 w-px bg-border/70" />
                <div className="relative pl-6">
                  <span className="absolute left-0 top-1.5 h-3 w-3 rounded-full bg-foreground" />
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-foreground">Associate Software Engineer</p>
                      <Badge variant="outline" className="border-border/60">Aug 2024 - Present</Badge>
                    </div>
                    <p className="text-xs uppercase tracking-[0.3em]">Nomura Research Institute & Financial Technology</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li>Architected a micro-services platform with Report and Workflow services on Java 21 and Spring Boot, integrating Camunda External Tasks and Saga orchestration.</li>
                      <li>Automated Hibernate/JPA layer generation, cutting dev time by 60% and standardizing service scaffolding.</li>
                      <li>Built a Docker-based CI/CD pipeline with Jenkins for streamlined releases.</li>
                      <li>Delivered a Python test-automation framework for OracleDB with a Streamlit chatbot, accelerating validation cycles by 60%.</li>
                      <li>Implemented an LLM-powered ATS using LlamaIndex, Cohere, and Pinecone, achieving 90%+ resume-matching accuracy.</li>
                    </ul>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="bg-muted/70">Java 21</Badge>
                      <Badge variant="secondary" className="bg-muted/70">Spring Boot</Badge>
                      <Badge variant="secondary" className="bg-muted/70">Camunda</Badge>
                      <Badge variant="secondary" className="bg-muted/70">Jenkins</Badge>
                    </div>
                  </div>
                </div>

                <div className="relative pl-6">
                  <span className="absolute left-0 top-1.5 h-3 w-3 rounded-full bg-foreground/60" />
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-foreground">Data Scientist</p>
                      <Badge variant="outline" className="border-border/60">Nov 2023 - Jun 2024</Badge>
                    </div>
                    <p className="text-xs uppercase tracking-[0.3em]">Omdena (Remote)</p>
                    <ul className="list-disc pl-5 space-y-1">
                      <li>Built XGBoost and LSTM time-series models for flood prediction with 92-95% accuracy.</li>
                      <li>Led a 10-member cross-functional team to deliver a production-ready forecasting pipeline.</li>
                    </ul>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="bg-muted/70">XGBoost</Badge>
                      <Badge variant="secondary" className="bg-muted/70">LSTM</Badge>
                      <Badge variant="secondary" className="bg-muted/70">Time Series</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass-panel border-border/60 hover-glow">
              <CardHeader>
                <CardTitle>University Projects</CardTitle>
                <CardDescription>AI systems with measurable outcomes.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-5 text-sm text-muted-foreground">
                <div className="rounded-2xl border border-border/60 bg-card/60 p-4 hover-glow">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-foreground">Nepali LLM - Tuned Language Model</p>
                    <Badge variant="secondary" className="bg-muted/70">NLU +25%</Badge>
                  </div>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Trained a SentencePiece tokenizer on a Nepali corpus, reducing token count by 80%.</li>
                    <li>Fine-tuned Gemma-2B via LoRA, boosting NLU task accuracy by 25%.</li>
                    <li>Deployed a Nepali chatbot with Streamlit, increasing user engagement by 30%.</li>
                  </ul>
                </div>

                <div className="rounded-2xl border border-border/60 bg-card/60 p-4 hover-glow">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-foreground">AuraSQL - AI-Powered Text2SQL Platform</p>
                    <Badge variant="secondary" className="bg-muted/70">Workflow -85%</Badge>
                  </div>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Built a RAG-powered Text2SQL system with multi-database connectivity and multi-table selection.</li>
                    <li>Integrated Cohere embeddings with schema context in Pinecone, powering OpenAI GPT-OSS 20B (Groq) via a Next.js dashboard with Supabase authentication.</li>
                    <li>Reduced manual query writing by 80% and workflow time by 85%.</li>
                  </ul>
                </div>

                <div className="rounded-2xl border border-border/60 bg-card/60 p-4 hover-glow">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-foreground">Professional-Grade RAG System</p>
                    <Badge variant="secondary" className="bg-muted/70">Hybrid Retrieval</Badge>
                  </div>
                  <ul className="list-disc pl-5 space-y-1">
                    <li>Engineered a production-ready RAG system using hybrid BM25 + semantic search, intelligent reranking, conversational context, and source attribution.</li>
                    <li>Maintained a multi-factor relevance scoring mechanism to rank document chunks with semantic and metadata signals.</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </section>

          <section className="glass-panel rounded-[28px] p-6 md:p-8 space-y-6">
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                <Sparkles className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h2 className="text-2xl md:text-3xl font-bold">Technical Proficiencies</h2>
                <p className="text-sm text-muted-foreground">Focused stack across AI, data, and platform engineering.</p>
              </div>
            </div>
            <div className="grid gap-6 md:grid-cols-2">
              {skillGroups.map((group) => (
                <div key={group.title} className="space-y-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{group.title}</p>
                  <div className="flex flex-wrap gap-2">
                    {group.items.map((item) => (
                      <Badge key={item} variant="secondary" className="bg-muted/70">
                        {item}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-6 md:grid-cols-2">
            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>Contact</CardTitle>
                <CardDescription>Reach out for collaboration or roles.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  shivam99806@gmail.com
                </p>
                <p className="flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  +91 8521846844
                </p>
                <div className="flex flex-wrap gap-3 pt-2">
                  <Button variant="outline" asChild>
                    <a href="https://linkedin.com/in/shivam-sourav-b889aa204/" target="_blank" rel="noreferrer">
                      <Linkedin className="h-4 w-4 mr-2" />
                      LinkedIn
                    </a>
                  </Button>
                  <Button variant="outline" asChild>
                    <a href="https://github.com/Shivam5560" target="_blank" rel="noreferrer">
                      <Github className="h-4 w-4 mr-2" />
                      GitHub
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="glass-panel border-border/60">
              <CardHeader>
                <CardTitle>Availability</CardTitle>
                <CardDescription>Open to impactful AI and data roles.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>Focused on RAG systems, orchestration, and applied ML in production.</p>
                <p>Interested in building scalable platforms with reliable evaluation and governance.</p>
                <div className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                  <span className="h-2 w-2 rounded-full bg-green-400 shadow-sm shadow-green-400/50" />
                  Available for collaboration
                </div>
              </CardContent>
            </Card>
          </section>

          <p className="text-xs text-muted-foreground">Note: Information is based on Shivam_AI.pdf and reflects current credentials and achievements.</p>
        </div>
      </main>
    </div>
  );
}
