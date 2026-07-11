export type Capability =
  | "auth"
  | "retrieval"
  | "sql"
  | "workflows"
  | "artifacts"
  | "evaluation"
  | "presentations"
  | "career"
  | "mcp";

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  starter_prompt: string;
}

export interface AppDependency {
  app_id: string;
  minimum_version: string;
}

export interface AppManifest {
  id: string;
  version: string;
  name: string;
  summary: string;
  category: string;
  icon: string;
  frontend_route: string;
  backend_route_prefixes: string[];
  backend_router_ids: string[];
  required_capabilities: Capability[];
  optional_capabilities: Capability[];
  required_permissions: string[];
  required_env_keys: string[];
  dependencies: AppDependency[];
  demo_scenarios: DemoScenario[];
  health_check_id: string;
  packaging_paths: string[];
}
