import { Header, Sidebar } from "@/components/layout";
{%- if cookiecutter.use_jwt or cookiecutter.use_api_key %}
import { AuthGuard } from "@/components/layout/auth-guard";
{%- endif %}
import { PageTransition } from "@/components/layout/page-transition";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
{%- if cookiecutter.use_jwt or cookiecutter.use_api_key %}
    <AuthGuard>
      <div className="flex h-screen flex-col">
        <Header />
        <Sidebar />
        <main className="flex min-h-0 flex-1 flex-col overflow-auto p-3 sm:p-6">
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </AuthGuard>
{%- else %}
    <div className="flex h-screen flex-col">
      <Header />
      <Sidebar />
      <main className="flex-1 overflow-auto p-3 sm:p-6">
        <PageTransition>{children}</PageTransition>
      </main>
    </div>
{%- endif %}
  );
}
