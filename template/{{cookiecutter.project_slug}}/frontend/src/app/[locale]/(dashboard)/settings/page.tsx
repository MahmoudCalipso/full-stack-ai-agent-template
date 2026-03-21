"use client";

import { Card, Badge } from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import { Server, Code, Shield, Palette } from "lucide-react";
import { Breadcrumb } from "@/components/layout/breadcrumb";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl pb-8">
      <Breadcrumb />
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Application configuration and preferences
        </p>
      </div>

      <div className="grid gap-4">
        {/* Appearance */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Palette className="h-5 w-5" />
            Appearance
          </h3>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-sm">Theme</p>
              <p className="text-xs text-muted-foreground">Choose light, dark, or system theme</p>
            </div>
            <ThemeToggle variant="dropdown" />
          </div>
        </Card>

        {/* Application Info */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Server className="h-5 w-5" />
            Application
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Project</span>
              <span className="font-medium">{{ cookiecutter.project_name }}</span>
            </div>
{%- if cookiecutter.enable_ai_agent %}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">AI Framework</span>
              <Badge variant="secondary">{{ cookiecutter.ai_framework }}</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">LLM Provider</span>
              <Badge variant="secondary">{{ cookiecutter.llm_provider }}</Badge>
            </div>
{%- endif %}
{%- if cookiecutter.enable_rag %}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Vector Store</span>
              <Badge variant="secondary">{{ cookiecutter.vector_store }}</Badge>
            </div>
{%- endif %}
          </div>
        </Card>

        {/* Stack Info */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Code className="h-5 w-5" />
            Stack
          </h3>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">FastAPI</Badge>
            <Badge variant="outline">Next.js 15</Badge>
{%- if cookiecutter.use_postgresql %}
            <Badge variant="outline">PostgreSQL</Badge>
{%- endif %}
{%- if cookiecutter.use_mongodb %}
            <Badge variant="outline">MongoDB</Badge>
{%- endif %}
{%- if cookiecutter.use_sqlite %}
            <Badge variant="outline">SQLite</Badge>
{%- endif %}
{%- if cookiecutter.enable_redis %}
            <Badge variant="outline">Redis</Badge>
{%- endif %}
{%- if cookiecutter.use_celery %}
            <Badge variant="outline">Celery</Badge>
{%- endif %}
{%- if cookiecutter.use_taskiq %}
            <Badge variant="outline">Taskiq</Badge>
{%- endif %}
{%- if cookiecutter.use_arq %}
            <Badge variant="outline">ARQ</Badge>
{%- endif %}
          </div>
        </Card>

        {/* Security */}
        <Card className="p-4 sm:p-6">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold">
            <Shield className="h-5 w-5" />
            Security
          </h3>
          <div className="space-y-3">
{%- if cookiecutter.use_jwt %}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Authentication</span>
              <Badge variant="outline">JWT</Badge>
            </div>
{%- endif %}
{%- if cookiecutter.use_api_key %}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">API Key</span>
              <Badge variant="outline">Enabled</Badge>
            </div>
{%- endif %}
{%- if cookiecutter.enable_rate_limiting %}
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Rate Limiting</span>
              <Badge variant="outline">{{ cookiecutter.rate_limit_requests }}/{{ cookiecutter.rate_limit_period }}s</Badge>
            </div>
{%- endif %}
          </div>
        </Card>
      </div>
    </div>
  );
}
