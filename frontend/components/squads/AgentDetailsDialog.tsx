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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { LLM_PROVIDERS } from '@/lib/constants';
import type { Agent } from '@/types/squad';

interface AgentDetailsDialogProps {
    agent: Agent | null;
    isOpen: boolean;
    onClose: () => void;
    onSave: (agentId: string, updates: Partial<Agent> & { system_prompt?: string; llm_config?: any }) => void;
}

export function AgentDetailsDialog({ agent, isOpen, onClose, onSave }: AgentDetailsDialogProps) {
    const [name, setName] = useState('');
    const [role, setRole] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [provider, setProvider] = useState('openai');
    const [model, setModel] = useState('gpt-4-turbo');
    const [apiKey, setApiKey] = useState('');

    useEffect(() => {
        if (agent) {
            setName(agent.name);
            setRole(agent.role);
            // Mock data for now since these fields aren't in the base type yet
            setSystemPrompt("You are a helpful AI assistant specialized in backend development.");
            setModel("gpt-4-turbo");
            setApiKey("sk-...");
        }
    }, [agent]);

    const handleProviderChange = (value: string) => {
        setProvider(value);
        const firstModel = LLM_PROVIDERS[value as keyof typeof LLM_PROVIDERS].models[0].id;
        setModel(firstModel);
    };

    const handleSave = () => {
        if (!agent) return;

        onSave(agent.id, {
            name,
            role,
            system_prompt: systemPrompt,
            llm_config: {
                model,
                api_key: apiKey
            }
        });
        onClose();
    };

    if (!agent) return null;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>Edit Agent: {agent.name}</DialogTitle>
                    <DialogDescription>
                        Configure agent settings, prompts, and LLM parameters.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-6 py-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="role">Role</Label>
                            <Input
                                id="role"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="system_prompt">System Prompt</Label>
                        <Textarea
                            id="system_prompt"
                            value={systemPrompt}
                            onChange={(e) => setSystemPrompt(e.target.value)}
                            className="h-32 font-mono text-sm"
                            placeholder="You are an expert developer..."
                        />
                    </div>

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
                        <Label htmlFor="api_key">API Key (Optional Override)</Label>
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
                    <Button onClick={handleSave}>Save Changes</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog >
    );
}
