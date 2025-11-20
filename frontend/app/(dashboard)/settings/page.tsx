'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/lib/store/auth';
import { authAPI } from '@/lib/api/auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  User,
  Building2,
  Key,
  Palette,
  Bell,
  Copy,
  Check,
  Eye,
  EyeOff,
  Plus,
  Trash2,
  Moon,
  Sun,
} from 'lucide-react';
import { useToast } from '@/lib/hooks/use-toast';

interface ApiKey {
  id: string;
  name: string;
  key: string;
  created_at: string;
  last_used?: string;
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const { toast } = useToast();

  // User Profile State
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [updatingProfile, setUpdatingProfile] = useState(false);

  // Organization State
  const [orgName, setOrgName] = useState('');
  const [orgDescription, setOrgDescription] = useState('');
  const [updatingOrg, setUpdatingOrg] = useState(false);

  // API Keys State
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [creatingKey, setCreatingKey] = useState(false);
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Theme State
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  // Notifications State
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [taskNotifications, setTaskNotifications] = useState(true);
  const [executionNotifications, setExecutionNotifications] = useState(true);

  useEffect(() => {
    // Load saved theme from localStorage
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      applyTheme(savedTheme);
    }

    // Load API keys (mock data for now)
    loadApiKeys();
  }, []);

  const loadApiKeys = () => {
    // Mock API keys - In production, fetch from backend
    const mockKeys: ApiKey[] = [
      {
        id: '1',
        name: 'Production API Key',
        key: 'sk_live_1234567890abcdef',
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        last_used: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: '2',
        name: 'Development API Key',
        key: 'sk_test_0987654321fedcba',
        created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
        last_used: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
      },
    ];
    setApiKeys(mockKeys);
  };

  const handleUpdateProfile = async () => {
    setUpdatingProfile(true);
    try {
      // In production, call API to update user profile
      // const updatedUser = await authAPI.updateProfile({ full_name: fullName, email });

      // Mock update
      await new Promise((resolve) => setTimeout(resolve, 1000));

      if (user) {
        const updatedUser = { ...user, full_name: fullName, email };
        setUser(updatedUser);
      }

      toast({
        title: 'Success',
        description: 'Profile updated successfully.',
      });
    } catch (error) {
      console.error('Failed to update profile:', error);
      toast({
        title: 'Error',
        description: 'Failed to update profile. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setUpdatingProfile(false);
    }
  };

  const handleUpdateOrg = async () => {
    setUpdatingOrg(true);
    try {
      // In production, call API to update organization
      await new Promise((resolve) => setTimeout(resolve, 1000));

      toast({
        title: 'Success',
        description: 'Organization settings updated successfully.',
      });
    } catch (error) {
      console.error('Failed to update organization:', error);
      toast({
        title: 'Error',
        description: 'Failed to update organization. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setUpdatingOrg(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a key name.',
        variant: 'destructive',
      });
      return;
    }

    setCreatingKey(true);
    try {
      // In production, call API to create key
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const newKey: ApiKey = {
        id: Date.now().toString(),
        name: newKeyName,
        key: `sk_live_${Math.random().toString(36).substring(2, 18)}`,
        created_at: new Date().toISOString(),
      };

      setApiKeys([...apiKeys, newKey]);
      setNewKeyName('');
      setRevealedKeys(new Set([...revealedKeys, newKey.id]));

      toast({
        title: 'Success',
        description: 'API key created successfully. Make sure to copy it now!',
      });
    } catch (error) {
      console.error('Failed to create API key:', error);
      toast({
        title: 'Error',
        description: 'Failed to create API key. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setCreatingKey(false);
    }
  };

  const handleDeleteApiKey = async (keyId: string) => {
    try {
      // In production, call API to delete key
      await new Promise((resolve) => setTimeout(resolve, 500));

      setApiKeys(apiKeys.filter((key) => key.id !== keyId));

      toast({
        title: 'Success',
        description: 'API key deleted successfully.',
      });
    } catch (error) {
      console.error('Failed to delete API key:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete API key. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const toggleKeyVisibility = (keyId: string) => {
    const newRevealed = new Set(revealedKeys);
    if (newRevealed.has(keyId)) {
      newRevealed.delete(keyId);
    } else {
      newRevealed.add(keyId);
    }
    setRevealedKeys(newRevealed);
  };

  const copyToClipboard = (key: string, keyId: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);

    toast({
      title: 'Copied',
      description: 'API key copied to clipboard.',
    });
  };

  const applyTheme = (newTheme: 'light' | 'dark') => {
    if (newTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleThemeToggle = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    applyTheme(newTheme);

    toast({
      title: 'Theme Updated',
      description: `Switched to ${newTheme} mode.`,
    });
  };

  const userInitials = user?.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase() || '??';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account settings and preferences
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList>
          <TabsTrigger value="profile">
            <User className="w-4 h-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="organization">
            <Building2 className="w-4 h-4 mr-2" />
            Organization
          </TabsTrigger>
          <TabsTrigger value="api-keys">
            <Key className="w-4 h-4 mr-2" />
            API Keys
          </TabsTrigger>
          <TabsTrigger value="appearance">
            <Palette className="w-4 h-4 mr-2" />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="w-4 h-4 mr-2" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and profile settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Avatar Section */}
              <div className="flex items-center gap-4">
                <Avatar className="h-20 w-20">
                  <AvatarFallback className="bg-blue-600 text-white text-2xl">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm font-medium">Profile Picture</p>
                  <p className="text-xs text-muted-foreground">
                    Click to upload a new avatar (coming soon)
                  </p>
                </div>
              </div>

              <Separator />

              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                />
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                />
                <p className="text-xs text-muted-foreground">
                  Your email is used for login and notifications
                </p>
              </div>

              {/* User ID */}
              <div className="space-y-2">
                <Label>User ID</Label>
                <div className="flex items-center gap-2">
                  <Input value={user?.id || ''} readOnly className="font-mono text-sm" />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => {
                      if (user?.id) {
                        navigator.clipboard.writeText(user.id);
                        toast({ title: 'Copied', description: 'User ID copied to clipboard.' });
                      }
                    }}
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Account Status */}
              <div className="space-y-2">
                <Label>Account Status</Label>
                <div className="flex items-center gap-2">
                  <Badge variant={user?.is_active ? 'default' : 'secondary'}>
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                  {user?.is_superuser && <Badge variant="outline">Superuser</Badge>}
                </div>
              </div>

              <Button onClick={handleUpdateProfile} disabled={updatingProfile}>
                {updatingProfile ? 'Saving...' : 'Save Changes'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Organization Tab */}
        <TabsContent value="organization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Organization Settings</CardTitle>
              <CardDescription>
                Manage your organization details and settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Organization ID */}
              <div className="space-y-2">
                <Label>Organization ID</Label>
                <div className="flex items-center gap-2">
                  <Input
                    value={user?.organization_id || 'Not assigned'}
                    readOnly
                    className="font-mono text-sm"
                  />
                  {user?.organization_id && (
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => {
                        if (user?.organization_id) {
                          navigator.clipboard.writeText(user.organization_id);
                          toast({
                            title: 'Copied',
                            description: 'Organization ID copied to clipboard.',
                          });
                        }
                      }}
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              <Separator />

              {/* Organization Name */}
              <div className="space-y-2">
                <Label htmlFor="orgName">Organization Name</Label>
                <Input
                  id="orgName"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Enter organization name"
                />
              </div>

              {/* Organization Description */}
              <div className="space-y-2">
                <Label htmlFor="orgDescription">Description</Label>
                <Input
                  id="orgDescription"
                  value={orgDescription}
                  onChange={(e) => setOrgDescription(e.target.value)}
                  placeholder="Enter organization description"
                />
              </div>

              <Button onClick={handleUpdateOrg} disabled={updatingOrg}>
                {updatingOrg ? 'Saving...' : 'Save Changes'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>
                Manage your API keys for programmatic access
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Create New Key */}
              <div className="flex gap-2">
                <Input
                  placeholder="Key name (e.g., Production API Key)"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateApiKey()}
                />
                <Button onClick={handleCreateApiKey} disabled={creatingKey}>
                  <Plus className="w-4 h-4 mr-2" />
                  {creatingKey ? 'Creating...' : 'Create Key'}
                </Button>
              </div>

              <Separator />

              {/* API Keys List */}
              <div className="space-y-4">
                {apiKeys.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Key className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No API keys yet</p>
                    <p className="text-xs mt-1">Create your first API key to get started</p>
                  </div>
                ) : (
                  apiKeys.map((apiKey) => (
                    <Card key={apiKey.id}>
                      <CardContent className="pt-6">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <p className="font-medium">{apiKey.name}</p>
                              <p className="text-xs text-muted-foreground">
                                Created {new Date(apiKey.created_at).toLocaleDateString()}
                              </p>
                              {apiKey.last_used && (
                                <p className="text-xs text-muted-foreground">
                                  Last used {new Date(apiKey.last_used).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteApiKey(apiKey.id)}
                            >
                              <Trash2 className="w-4 h-4 text-red-600" />
                            </Button>
                          </div>

                          <div className="flex items-center gap-2">
                            <Input
                              value={
                                revealedKeys.has(apiKey.id)
                                  ? apiKey.key
                                  : '•'.repeat(apiKey.key.length)
                              }
                              readOnly
                              className="font-mono text-sm"
                            />
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => toggleKeyVisibility(apiKey.id)}
                            >
                              {revealedKeys.has(apiKey.id) ? (
                                <EyeOff className="w-4 h-4" />
                              ) : (
                                <Eye className="w-4 h-4" />
                              )}
                            </Button>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={() => copyToClipboard(apiKey.key, apiKey.id)}
                            >
                              {copiedKey === apiKey.id ? (
                                <Check className="w-4 h-4 text-green-600" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Appearance Tab */}
        <TabsContent value="appearance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                Customize the look and feel of the application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Theme Toggle */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label>Theme</Label>
                  <p className="text-sm text-muted-foreground">
                    Choose between light and dark mode
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Sun className="w-4 h-4" />
                  <Switch checked={theme === 'dark'} onCheckedChange={handleThemeToggle} />
                  <Moon className="w-4 h-4" />
                </div>
              </div>

              <Separator />

              {/* Current Theme Display */}
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  {theme === 'dark' ? (
                    <Moon className="w-5 h-5" />
                  ) : (
                    <Sun className="w-5 h-5" />
                  )}
                  <p className="font-medium">
                    Current Theme: {theme === 'dark' ? 'Dark' : 'Light'}
                  </p>
                </div>
                <p className="text-sm text-muted-foreground">
                  {theme === 'dark'
                    ? 'Dark mode is enabled. Your eyes will thank you!'
                    : 'Light mode is enabled. Bright and clear!'}
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Configure how you want to receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Email Notifications */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive email updates about your account
                  </p>
                </div>
                <Switch
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                />
              </div>

              <Separator />

              {/* Task Notifications */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label>Task Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when tasks are assigned or completed
                  </p>
                </div>
                <Switch checked={taskNotifications} onCheckedChange={setTaskNotifications} />
              </div>

              <Separator />

              {/* Execution Notifications */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label>Execution Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive updates when executions complete or fail
                  </p>
                </div>
                <Switch
                  checked={executionNotifications}
                  onCheckedChange={setExecutionNotifications}
                />
              </div>

              <Separator />

              <Button
                onClick={() => {
                  toast({
                    title: 'Settings Saved',
                    description: 'Your notification preferences have been updated.',
                  });
                }}
              >
                Save Preferences
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
