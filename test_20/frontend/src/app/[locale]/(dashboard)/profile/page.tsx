"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { useAuth } from "@/hooks";
import { useAuthStore } from "@/stores";
import { apiClient, ApiError } from "@/lib/api-client";
import type { User, Session, SessionListResponse } from "@/types";
import {
  Button, Card, CardHeader, CardTitle, CardContent, Input, Label, Badge, Skeleton,
  AlertDialog, AlertDialogTrigger, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui";
import { ThemeToggle } from "@/components/theme";
import { User as UserIcon, Mail, Calendar, Shield, Settings, Monitor, Smartphone, Globe, Trash2, Link2, Palette, LogOut } from "lucide-react";
import { Breadcrumb } from "@/components/layout/breadcrumb";
import { GoogleIcon } from "@/components/icons/google-icon";

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function DeviceIcon({ type }: { type?: string | null }) {
  if (type === "mobile") return <Smartphone className="h-4 w-4" />;
  if (type === "desktop") return <Monitor className="h-4 w-4" />;
  return <Globe className="h-4 w-4" />;
}

export default function ProfilePage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { setUser } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [editEmail, setEditEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await apiClient.get<SessionListResponse>("/sessions");
      setSessions(data.sessions);
    } catch {
      // Sessions endpoint may not be available
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const handleEdit = () => {
    if (!isEditing && user) {
      setEditEmail(user.email);
    }
    setIsEditing(!isEditing);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await apiClient.patch<User>("/users/me", { email: editEmail });
      setUser(updated);
      toast.success("Profile updated");
      setIsEditing(false);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Failed to update profile";
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      await apiClient.delete(`/sessions/${sessionId}`);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      toast.success("Session revoked");
    } catch {
      toast.error("Failed to revoke session");
    }
  };

  const handleRevokeAll = async () => {
    try {
      await apiClient.delete("/sessions");
      setSessions([]);
      toast.success("All other sessions revoked");
    } catch {
      toast.error("Failed to revoke sessions");
    }
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Card className="mx-4 p-6 text-center sm:p-8">
          <p className="text-muted-foreground">Please log in to view your profile.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-8">
      <Breadcrumb />
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="bg-primary/10 flex h-14 w-14 shrink-0 items-center justify-center rounded-full">
            <UserIcon className="text-primary h-7 w-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{user.email}</h1>
            <div className="mt-1 flex items-center gap-2">
              {user.is_superuser && (
                <Badge variant="secondary"><Shield className="mr-1 h-3 w-3" />Admin</Badge>
              )}
              {user.is_active && (
                <Badge variant="outline" className="text-green-600">Active</Badge>
              )}
              {user.created_at && (
                <span className="text-muted-foreground text-xs">
                  Since {new Date(user.created_at).toLocaleDateString()}
                </span>
              )}
            </div>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={handleEdit} className="h-10 self-start">
          <Settings className="mr-2 h-4 w-4" />
          {isEditing ? "Cancel" : "Edit Profile"}
        </Button>
      </div>

      {/* Main grid — 2 columns on desktop */}
      <div className="grid gap-4 lg:grid-cols-5 sm:gap-6">
        {/* Left column — 3/5 */}
        <div className="space-y-4 lg:col-span-3 sm:space-y-6">
          {/* Account Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Mail className="h-4 w-4" />
                Account Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="email" className="text-sm">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={isEditing ? editEmail : user.email}
                    onChange={(e) => setEditEmail(e.target.value)}
                    disabled={!isEditing}
                    className={!isEditing ? "bg-muted" : ""}
                  />
                </div>
                {isEditing && (
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={handleEdit} size="sm">Cancel</Button>
                    <Button onClick={handleSave} disabled={isSaving} size="sm">
                      {isSaving ? "Saving..." : "Save Changes"}
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Active Sessions */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Monitor className="h-4 w-4" />
                Active Sessions
              </CardTitle>
              {sessions.length > 1 && (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm" className="text-xs">Revoke all others</Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Revoke all other sessions?</AlertDialogTitle>
                      <AlertDialogDescription>This will sign you out from all other devices.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={handleRevokeAll}>Revoke all</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              )}
            </CardHeader>
            <CardContent>
              {sessionsLoading ? (
                <div className="space-y-2">
                  {[1, 2].map(i => <Skeleton key={i} className="h-14 w-full rounded-lg" />)}
                </div>
              ) : sessions.length === 0 ? (
                <p className="text-muted-foreground text-sm">No active sessions found</p>
              ) : (
                <div className="space-y-2">
                  {sessions.map(session => (
                    <div key={session.id} className="flex items-center justify-between rounded-lg border p-3">
                      <div className="flex items-center gap-3">
                        <div className="text-muted-foreground"><DeviceIcon type={session.device_type} /></div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium">{session.device_name || "Unknown device"}</p>
                            {session.is_current && <Badge variant="secondary" className="text-[10px]">Current</Badge>}
                          </div>
                          <p className="text-muted-foreground text-xs">
                            {session.ip_address && `${session.ip_address} · `}
                            Last active {timeAgo(session.last_used_at)}
                          </p>
                        </div>
                      </div>
                      {!session.is_current && (
                        <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive h-8" onClick={() => handleRevokeSession(session.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column — 2/5 */}
        <div className="space-y-4 lg:col-span-2 sm:space-y-6">
          {/* Connected Accounts */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Link2 className="h-4 w-4" />
                Connected Accounts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between rounded-lg border p-3">
                <div className="flex items-center gap-3">
                  <GoogleIcon className="h-5 w-5" />
                  <div>
                    <p className="text-sm font-medium">Google</p>
                    <p className="text-muted-foreground text-xs">
                      {user.oauth_provider === "google" ? "Connected" : "Not connected"}
                    </p>
                  </div>
                </div>
                {user.oauth_provider === "google" ? (
                  <Badge variant="secondary" className="text-green-600">Connected</Badge>
                ) : (
                  <Button variant="outline" size="sm" onClick={() => { window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/oauth/google/login`; }}>
                    Connect
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Preferences */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Palette className="h-4 w-4" />
                Preferences
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Theme</p>
                  <p className="text-muted-foreground text-xs">Color scheme</p>
                </div>
                <ThemeToggle variant="dropdown" />
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-destructive/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-destructive flex items-center gap-2 text-sm font-semibold">
                <LogOut className="h-4 w-4" />
                Danger Zone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">Sign out</p>
                  <p className="text-muted-foreground text-xs">Sign out from this device</p>
                </div>
                <Button variant="destructive" size="sm" onClick={logout}>
                  Sign Out
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
