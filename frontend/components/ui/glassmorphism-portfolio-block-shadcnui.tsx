"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { motion, Variants } from "framer-motion"
import { useEffect, useState } from "react"
import type { LucideIcon } from "lucide-react"
import { ArrowUpRight, Github, Linkedin, Mail, Phone } from "lucide-react"

type Highlight = {
  title: string
  description: string
}

type SocialLink = {
  label: string
  handle: string
  href: string
  icon: LucideIcon
  external?: boolean
}

type WorkExperience = {
  role: string
  company: string
  period: string
  summary: string
}

type FeaturedProject = {
  title: string
  metric: string
  summary: string
}

type GlassmorphismPortfolioBlockProps = {
  profileImageSrc?: string
}

const highlights: Highlight[] = [
  {
    title: "Current Role",
    description:
      "Associate Software Engineer at Nomura Fintech building micro-services, workflow orchestration, and AI-driven automation.",
  },
  {
    title: "Core Expertise",
    description:
      "Production RAG systems, LLM-powered ATS matching, schema-aware Text2SQL, and end-to-end platform engineering.",
  },
  {
    title: "Availability",
    description:
      "Open to impactful AI and data roles · Available for collaboration across India, EU, and US time zones.",
  },
]

const socialLinks: SocialLink[] = [
  {
    label: "LinkedIn",
    handle: "Shivam Sourav",
    href: "https://linkedin.com/in/shivam-sourav-b889aa204/",
    icon: Linkedin,
    external: true,
  },
  {
    label: "GitHub",
    handle: "Shivam5560",
    href: "https://github.com/Shivam5560",
    icon: Github,
    external: true,
  },
  {
    label: "Email",
    handle: "shivam99806@gmail.com",
    href: "mailto:shivam99806@gmail.com",
    icon: Mail,
  },
  {
    label: "Phone",
    handle: "+91 8521846844",
    href: "tel:+918521846844",
    icon: Phone,
  },
]

const workExperiences: WorkExperience[] = [
  {
    role: "Associate Software Engineer",
    company: "Nomura Fintech",
    period: "Aug 2024 - Present",
    summary:
      "Built micro-services with Java 21 and Spring Boot, integrated Camunda workflows, and delivered automation that reduced development and validation effort.",
  },
  {
    role: "Data Scientist",
    company: "Omdena",
    period: "Nov 2023 - Jun 2024",
    summary:
      "Developed XGBoost and LSTM flood prediction pipelines with high accuracy and led cross-functional collaboration for deployment-ready outcomes.",
  },
]

const featuredProjects: FeaturedProject[] = [
  {
    title: "AuraSQL - AI Text2SQL Platform",
    metric: "Workflow -85%",
    summary:
      "Built RAG-powered Text2SQL with multi-database support and schema-aware generation in a Next.js dashboard.",
  },
  {
    title: "Professional-Grade RAG System",
    metric: "Hybrid Retrieval",
    summary:
      "Engineered BM25 + semantic retrieval, reranking, context memory, and source attribution for reliable answers.",
  },
  {
    title: "Nepali LLM",
    metric: "NLU +25%",
    summary:
      "Fine-tuned Gemma-2B with LoRA after tokenizer optimization to improve Nepali language understanding.",
  },
]


const listVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.4,
      staggerChildren: 0.08,
    },
  },
}

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.35,
    },
  },
}

export function GlassmorphismPortfolioBlock({
  profileImageSrc = "/images/developer/profile-main.png",
}: GlassmorphismPortfolioBlockProps) {
  const [resolvedImageSrc, setResolvedImageSrc] = useState(profileImageSrc)

  useEffect(() => {
    setResolvedImageSrc(profileImageSrc)
  }, [profileImageSrc])

  return (
    <section className="relative min-h-screen overflow-hidden px-6 py-24 lg:py-32">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative overflow-hidden rounded-3xl border border-border/50 bg-background/45 p-8 backdrop-blur-2xl md:p-12"
        >
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-foreground/[0.05] via-transparent to-transparent" />

          <div className="relative grid gap-12 lg:grid-cols-2">
            <div className="space-y-8">
              <Badge
                variant="outline"
                className="inline-flex items-center gap-2 rounded-full border-border/50 bg-background/55 px-4 py-1.5 text-xs uppercase tracking-[0.3em] text-foreground/70 backdrop-blur transition-colors hover:bg-background/70"
              >
                Developer Profile
              </Badge>

              <div className="space-y-4">
                <motion.h2
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.1 }}
                  className="text-2xl font-semibold tracking-tight text-foreground md:text-3xl"
                >
                  Shivam Sourav, AI Engineer & Software Developer
                </motion.h2>
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  className="max-w-xl text-base leading-relaxed text-foreground/70 md:text-md"
                >
                  B.Tech in AI & Data Science focused on production-grade RAG platforms, workflow-driven systems, and measurable business impact through applied machine learning.
                </motion.p>
              </div>

              <div className="grid gap-4 sm:grid-cols-1">
                {highlights.map((item, index) => (
                  <motion.div
                    key={item.title}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: 0.1 * index }}
                    whileHover={{ y: -4 }}
                    className="group relative overflow-hidden rounded-2xl border border-border/40 bg-background/60 p-5 backdrop-blur transition-all hover:border-border/60 hover:shadow-lg"
                  >
                    <div className="absolute inset-0 -z-10 bg-gradient-to-br from-foreground/[0.04] via-transparent to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                    <div className="relative space-y-2">
                      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/40">
                        {item.title}
                      </p>
                      <p className="text-sm leading-relaxed text-foreground/70">
                        {item.description}
                      </p>
                    </div>
                  </motion.div>
                ))}
              </div>

              <div className="space-y-3 rounded-2xl border border-border/40 bg-background/60 p-5 backdrop-blur">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-foreground/40">
                  Work Experience
                </p>
                <div className="space-y-3">
                  {workExperiences.map((experience) => (
                    <div key={`${experience.role}-${experience.company}`} className="rounded-xl border border-border/40 bg-background/60 p-3">
                      <p className="text-sm font-semibold text-foreground">{experience.role}</p>
                      <p className="text-xs text-foreground/65">{experience.company} · {experience.period}</p>
                      <p className="mt-1 text-xs leading-relaxed text-foreground/70">{experience.summary}</p>
                    </div>
                  ))}
                </div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="grid grid-cols-1 gap-4"
              >
                <Button
                  size="lg"
                  onClick={() => window.open("https://github.com/Shivam5560", "_blank")}
                  className="h-12 w-full gap-2 rounded-full px-8 text-sm uppercase tracking-[0.25em] transition-all hover:shadow-lg sm:w-auto"
                >
                  View projects
                  <ArrowUpRight className="h-4 w-4" />
                </Button>
              </motion.div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 rounded-[32px] bg-gradient-to-b from-primary/15 via-transparent to-transparent blur-3xl" />
              <div className="relative flex h-full flex-col justify-between overflow-hidden rounded-[28px] border border-border/50 bg-background/60 p-8 backdrop-blur-xl">
                <div className="flex flex-col items-center text-center">
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5 }}
                    className="relative mb-6"
                  >
                    <div className="absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/20 blur-2xl" />
                    <img
                      src={resolvedImageSrc}
                      alt="Shivam Sourav"
                      onError={(event) => {
                        const fallback = "https://images.unsplash.com/photo-1544723795-3fb6469f5b39?w=640&q=80"
                        if (event.currentTarget.src !== fallback) {
                          setResolvedImageSrc(fallback)
                        }
                      }}
                      className="relative h-32 w-32 rounded-full border border-border/40 object-cover shadow-[0_25px_60px_rgba(15,23,42,0.3)] dark:shadow-[0_25px_60px_rgba(0,0,0,0.6)]"
                    />
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="space-y-1"
                  >
                    <h3 className="text-2xl font-semibold tracking-tight text-foreground">
                      Shivam Sourav
                    </h3>
                    <p className="text-xs font-semibold uppercase tracking-[0.35em] text-foreground/45">
                      Software Engineer · AI Systems
                    </p>
                  </motion.div>

                  <motion.p
                    initial={{ opacity: 0, y: 10 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                    className="mt-4 max-w-sm text-sm leading-relaxed text-foreground/70"
                  >
                    Building reliable AI applications with hybrid retrieval, confidence-aware responses, and developer-first platform workflows.
                  </motion.p>

                  <div className="mt-6 w-full space-y-2 text-left">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-foreground/45">
                      Featured Projects
                    </p>
                    {featuredProjects.map((project) => (
                      <div key={project.title} className="rounded-xl border border-border/40 bg-background/60 p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs font-semibold text-foreground">{project.title}</p>
                          <span className="text-[10px] uppercase tracking-[0.2em] text-foreground/55">{project.metric}</span>
                        </div>
                        <p className="mt-1 text-xs leading-relaxed text-foreground/65">{project.summary}</p>
                      </div>
                    ))}
                  </div>

                </div>

                <motion.div
                  variants={listVariants}
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true, margin: "-80px" }}
                  className="mt-8 flex flex-col gap-3"
                >
                  {socialLinks.map((social) => {
                    const Icon = social.icon
                    return (
                      <motion.a
                        key={social.label}
                        variants={itemVariants}
                        href={social.href}
                        target={social.external ? "_blank" : undefined}
                        rel={social.external ? "noopener noreferrer" : undefined}
                        className="group flex items-center justify-between rounded-2xl border border-border/40 bg-background/70 px-4 py-3 text-left transition-all hover:-translate-y-0.5 hover:border-border/60 hover:bg-background/80 hover:shadow-md"
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.985 }}
                      >
                        <div className="flex items-center gap-3">
                          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-border/40 bg-background/70 text-foreground/80 shadow-[0_10px_30px_rgba(15,23,42,0.2)] transition-all group-hover:shadow-[0_10px_30px_rgba(15,23,42,0.3)] dark:shadow-[0_10px_30px_rgba(0,0,0,0.4)] dark:group-hover:shadow-[0_10px_30px_rgba(0,0,0,0.5)]">
                            <Icon className="h-4 w-4" />
                          </span>
                          <div>
                            <p className="text-sm font-semibold text-foreground">
                              {social.label}
                            </p>
                            <p className="text-xs text-foreground/60">
                              {social.handle}
                            </p>
                          </div>
                        </div>
                        <ArrowUpRight className="h-4 w-4 text-foreground/40 transition-all group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-foreground/70" />
                      </motion.a>
                    )
                  })}
                </motion.div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
