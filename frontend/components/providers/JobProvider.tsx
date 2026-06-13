"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useToast } from "@/hooks/useToast";

export interface Job {
  id: string;
  type: string;
  status: "pending" | "running" | "success" | "error";
  message?: string;
}

interface JobContextType {
  activeJobs: Job[];
  addJob: (job: Job) => void;
  removeJob: (id: string) => void;
  isJobActive: (type: string) => boolean;
}

const JobContext = createContext<JobContextType | undefined>(undefined);

export function JobProvider({ children }: { children: React.ReactNode }) {
  const [activeJobs, setActiveJobs] = useState<Job[]>([]);
  const { toast } = useToast();

  const addJob = useCallback((job: Job) => {
    setActiveJobs((prev) => {
      // Prevent duplicates
      if (prev.some(j => j.id === job.id)) {
        return prev;
      }
      return [...prev, job];
    });
  }, []);

  const removeJob = useCallback((id: string) => {
    setActiveJobs((prev) => prev.filter(j => j.id !== id));
  }, []);

  const isJobActive = useCallback((type: string) => {
    return activeJobs.some((job) => job.type === type && (job.status === "pending" || job.status === "running"));
  }, [activeJobs]);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimeout: NodeJS.Timeout;

    const connect = () => {
      const token = typeof window !== "undefined" ? window.localStorage.getItem("token") || "" : "";
      const wsUrl = `ws://localhost:8000/api/v1/ws/notifications?token=${token}`;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("JobContext WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "job_completed" || data.type === "job_failed") {
            const status = data.status; // success or error
            const message = data.message;
            const jobId = data.job_id;
            const jobType = data.job_type;
            
            // Remove the job from activeJobs
            setActiveJobs((prev) => prev.filter((j) => j.id !== jobId));
            
            toast({
              title: data.type === "job_completed" ? "Job Completed" : "Job Failed",
              description: message || `Job ${jobType} finished with status ${status}`,
              variant: data.type === "job_failed" ? "destructive" : "default",
            });
          } else if (data.type === "job_started" || data.type === "job_progress") {
            // Optional: update job progress
            setActiveJobs((prev) => 
              prev.map(j => j.id === data.job_id ? { ...j, status: "running", message: data.message } : j)
            );
          }
        } catch (err) {
          console.error("Failed to parse websocket message", err);
        }
      };

      ws.onclose = () => {
        console.log("JobContext WebSocket disconnected, reconnecting...");
        reconnectTimeout = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error("JobContext WebSocket error", err);
        ws.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) {
        // Prevent reconnect on unmount
        ws.onclose = null;
        ws.close();
      }
    };
  }, [toast]);

  return (
    <JobContext.Provider value={{ activeJobs, addJob, removeJob, isJobActive }}>
      {children}
    </JobContext.Provider>
  );
}

export function useJobs() {
  const context = useContext(JobContext);
  if (!context) {
    throw new Error("useJobs must be used within a JobProvider");
  }
  return context;
}
