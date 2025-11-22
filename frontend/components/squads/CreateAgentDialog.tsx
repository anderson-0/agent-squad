'use client';

import { useState, useEffect } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { AGENT_TEMPLATES, LLM_PROVIDERS } from '@/lib/constants';

interface CreateAgentDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (agent: { name: string; role: string; system_prompt: string; llm_config: any }) => void;
}

export function CreateAgentDialog({ isOpen, onClose, onSubmit }: CreateAgentDialogProps) {
    const [templateId, setTemplateId] = useState('');
    const [name, setName] = useState('');
    const [role, setRole] = useState('');
    const [useCustomPrompt, setUseCustomPrompt] = useState(false);
    const [systemPrompt, setSystemPrompt] = useState('');
    const [provider, setProvider] = useState('openai');
    const [model, setModel] = useState('gpt-4-turbo');
    const [apiKey, setApiKey] = useState('');

    // Handle template selection
    const handleTemplateChange = (value: string) => {
        setTemplateId(value);
        const template = AGENT_TEMPLATES.find(t => t.id === value);
        if (template) {
            setName(template.name);
            setRole(template.role);
            setSystemPrompt(template.prompt);
        }
    };

    // Handle provider change
    const handleProviderChange = (value: string) => {
        setProvider(value);
        // Reset model to first available for this provider
        const firstModel = LLM_PROVIDERS[value as keyof typeof LLM_PROVIDERS].models[0].id;
        setModel(firstModel);
    };

    const handleSubmit = () => {
        onSubmit({
            name,
            role,
            system_prompt: systemPrompt,
            llm_config: {
                provider,
                model,
                api_key: apiKey
            }
        });
        // Reset form
        setTemplateId('');
        setName('');
        setRole('');
        setUseCustomPrompt(false);
        setSystemPrompt('');
        setProvider('openai');
        setModel('gpt-4-turbo');
        setApiKey('');
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>Create New Agent</DialogTitle>
                    <DialogDescription>
                        Select a template or configure a custom AI agent.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-6 py-4">
                    {/* Template Selection */}
                    <div className="grid gap-2">
                        <Label htmlFor="template">Agent Template</Label>
                        <Select value={templateId} onValueChange={handleTemplateChange}>
                            <SelectTrigger id="template">
                                <SelectValue placeholder="Select a template..." />
                            </SelectTrigger>
                            <SelectContent>
                                {AGENT_TEMPLATES.map((t) => (
                                    <SelectItem key={t.id} value={t.id}>{t.name}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Agent Name"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="role">Role</Label>
                            <Input
                                id="role"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                placeholder="Agent Role"
                            />
                        </div>
                    </div>

                    {/* System Prompt Configuration */}
                    <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="custom_prompt"
                                checked={useCustomPrompt}
                                onCheckedChange={(checked) => setUseCustomPrompt(checked as boolean)}
                            />
                            <Label htmlFor="custom_prompt" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                Use custom system prompt
                            </Label>
                        </div>

                        {useCustomPrompt && (
                            <div className="grid gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
                                <Label htmlFor="system_prompt">System Prompt</Label>
                                <Textarea
                                    id="system_prompt"
                                    value={systemPrompt}
                                    onChange={(e) => setSystemPrompt(e.target.value)}
                                    className="h-32 font-mono text-sm"
                                    placeholder="You are an expert..."
                                />
                            </div>
                        )}
                    </div>

                    {/* LLM Configuration */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="provider">LLM Provider</Label>
                            <Select value={provider} onValueChange={handleProviderChange}>
                                <SelectTrigger id="provider">
                                    <SelectValue placeholder="Select provider" />
                                </SelectTrigger>
                                <SelectContent>
                                    {Object.entries(LLM_PROVIDERS).map(([key, config]) => (
                                        <SelectItem key={key} value={key}>{config.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="model">Model</Label>
                            <Select value={model} onValueChange={setModel}>
                                <SelectTrigger id="model">
                                    <SelectValue placeholder="Select model" />
                                </SelectTrigger>
                                <SelectContent>
                                    {LLM_PROVIDERS[provider as keyof typeof LLM_PROVIDERS].models.map((m) => (
                                        <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="api_key">API Key (Optional)</Label>
                        <Input
                            id="api_key"
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Leave empty to use squad default"
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>Cancel</Button>
                    <Button onClick={handleSubmit}>Create Agent</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
