"use client";

import { useCallback, useState } from "react";
import { Button } from "./ui/button";

interface InputSectionProps {
  onProcess: (data: { type: 'file' | 'text', payload: File | string }) => void;
  isLoading: boolean;
}

export default function InputSection({ onProcess, isLoading }: InputSectionProps) {
  const [activeTab, setActiveTab] = useState<'upload' | 'paste'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [textData, setTextData] = useState("");

  const onFiles = useCallback((incoming: FileList | null) => {
    if (!incoming || incoming.length === 0) return;
    setFile(incoming[0]); // Only taking the first file for now
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    onFiles(e.dataTransfer.files);
  }, [onFiles]);

  const handleAnalyze = () => {
    // Validate text input
    if (activeTab === 'paste' && textData.trim()) {
      const text = textData.trim();
      
      // Check minimum length
      if (text.length < 20) {
        alert("❌ Input is too short.\n\nPlease provide a detailed role description with responsibilities (minimum 20 characters).\n\nExample: 'KYC Analyst responsible for customer due diligence and identity verification'");
        return;
      }
      
      // Check minimum words
      const words = text.split(/\s+/);
      if (words.length < 3) {
        alert("❌ Input is too brief.\n\nPlease provide a complete role description.\n\nExample: 'AML Investigator responsible for investigating suspicious transactions and filing SARs'");
        return;
      }
      
      // Check for role-related context
      const roleKeywords = [
        'analyst', 'officer', 'manager', 'advisor', 'specialist', 'director', 
        'investigator', 'coordinator', 'supervisor', 'consultant', 'executive',
        'responsible', 'duties', 'tasks', 'role', 'position', 'job', 'work',
        'monitoring', 'compliance', 'kyc', 'aml', 'risk', 'due diligence',
        'customer', 'investigation', 'screening', 'reporting', 'oversight'
      ];
      
      const hasRoleContext = roleKeywords.some(keyword => 
        text.toLowerCase().includes(keyword)
      );
      
      if (!hasRoleContext) {
        alert("❌ Input does not appear to be a role description.\n\nPlease provide information about a job role with responsibilities.\n\nExample: 'Compliance Officer responsible for monitoring regulatory changes and ensuring AML policy compliance'");
        return;
      }
      
      onProcess({ type: 'text', payload: textData });
    } else if (activeTab === 'upload' && file) {
      onProcess({ type: 'file', payload: file });
    }
  };

  return (
    <div className="w-full max-w-3xl border rounded-lg overflow-hidden bg-card text-card-foreground shadow-sm">
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab('upload')}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            activeTab === 'upload' ? 'bg-primary/10 text-primary border-b-2 border-primary' : 'text-muted-foreground hover:bg-muted/50'
          }`}
        >
          Upload Document
        </button>
        <button
          onClick={() => setActiveTab('paste')}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            activeTab === 'paste' ? 'bg-primary/10 text-primary border-b-2 border-primary' : 'text-muted-foreground hover:bg-muted/50'
          }`}
        >
          Paste Text
        </button>
      </div>

      <div className="p-6">
        {activeTab === 'upload' ? (
          <div className="flex flex-col gap-4">
            <div
              onDrop={onDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border-2 border-dashed border-border rounded-lg p-8 bg-muted/20 flex flex-col items-center justify-center text-center transition-colors hover:bg-muted/40"
            >
              <p className="font-medium">Drag & drop a file here</p>
              <p className="text-sm text-muted-foreground mb-4">Supports PDF, DOCX, TXT</p>
              
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(e) => onFiles(e.target.files)}
                className="hidden"
                id="file-input"
              />
              <Button
                variant="outline"
                onClick={() => document.getElementById("file-input")?.click()}
              >
                Select File
              </Button>
            </div>
            
            {file && (
              <div className="rounded-md bg-muted/50 p-3 flex justify-between items-center text-sm">
                <span className="font-medium truncate">{file.name}</span>
                <span className="text-muted-foreground">{Math.round(file.size / 1024)} KB</span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-md p-3 text-sm">
              <p className="font-medium text-blue-900 dark:text-blue-100 mb-1">💡 Provide a detailed role description</p>
              <p className="text-blue-700 dark:text-blue-300 text-xs">
                Example: "KYC Analyst responsible for customer due diligence, identity verification, and risk assessment"
              </p>
            </div>
            <textarea 
              value={textData}
              onChange={(e) => setTextData(e.target.value)}
              placeholder="Example: AML Investigator responsible for investigating suspicious transactions, reviewing alerts, and filing SARs..."
              className="w-full min-h-[200px] p-3 rounded-md border border-input bg-transparent text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <Button 
            onClick={handleAnalyze} 
            disabled={isLoading || (activeTab === 'upload' && !file) || (activeTab === 'paste' && !textData.trim())}
          >
            {isLoading ? 'Processing...' : 'Analyze & Generate Training'}
          </Button>
        </div>
      </div>
    </div>
  );
}
