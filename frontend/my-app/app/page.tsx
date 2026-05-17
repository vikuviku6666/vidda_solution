"use client";

import { useState } from "react";
import Image from "next/image";
import axios from "axios";
import InputSection from "../components/Upload";
import ExplainabilityPanel from "../components/ExplainabilityPanel";
import Timeline from "../components/Timeline";
import ApprovalWorkflow from "../components/ApprovalWorkflow";
import ExportControls from "../components/ExportControls";
import ConfidenceBadge from "../components/ConfidenceBadge";
import BehaviouralOutcomes from "../components/BehaviouralOutcomes";
import GovernanceDashboard from "../components/GovernanceDashboard";
import SavedPlansPanel from "../components/SavedPlansPanel";
import PlanScorecard from "../components/PlanScorecard";
import { Button } from "../components/ui/button";

const quarters = [
  { key: "Q1", title: "Foundation" },
  { key: "Q2", title: "Application" },
  { key: "Q3", title: "Deepening" },
  { key: "Q4", title: "Embedding" },
];

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("");
  const [workflowData, setWorkflowData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [planRefresh, setPlanRefresh] = useState(0);

  const fetchWorkflowStatus = async (planId: string) => {
    // Fetch the updated plan from backend after revision
    try {
      console.log(`Fetching updated plan: ${planId}`);
      const response = await axios.get(`http://127.0.0.1:8000/workflow/plan/${planId}`);
      setWorkflowData(response.data);
      console.log("Plan data reloaded successfully");
    } catch (err: any) {
      console.error("Error fetching updated plan:", err);
      setError("Failed to reload updated plan: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleProcess = async (data: { type: 'file' | 'text', payload: File | string }) => {
    setIsLoading(true);
    setError(null);
    setLoadingStage("Analyzing role description...");
    
    try {
      let textToProcess = "";
      
      if (data.type === 'file') {
        const formData = new FormData();
        formData.append("file", data.payload as File);
        // Ensure backend is running on 8000
        const res = await axios.post("http://127.0.0.1:8000/upload", formData);
        textToProcess = res.data.text;
      } else {
        textToProcess = data.payload as string;
      }
      
      // Show progress stages
      setTimeout(() => setLoadingStage("Searching AMLR regulations..."), 3000);
      setTimeout(() => setLoadingStage("Extracting compliance requirements..."), 8000);
      setTimeout(() => setLoadingStage("Generating quarterly training plan..."), 15000);
      
      const workflowRes = await axios.post("http://127.0.0.1:8000/workflow/run", {
        uploaded_text: textToProcess
      });
      
      setWorkflowData(workflowRes.data);
      setLoadingStage("");
      setPlanRefresh(r => r + 1); // refresh saved plans panel
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || "An error occurred during processing.");
      setLoadingStage("");
    } finally {
      setIsLoading(false);
    }
  };

  const modules = workflowData?.recommendations?.map((rec: any, idx: number) => {
    // Normalize quarter format - backend returns "Q1 Foundation", "Q2 Application", etc.
    let quarter = rec.quarter;
    if (quarter) {
      // Extract just "Q1", "Q2", etc. from "Q1 Foundation", "Q2 Application"
      const match = quarter.match(/Q[1-4]/);
      quarter = match ? match[0] : `Q${(idx % 4) + 1}`;
    } else {
      // Distribute evenly across quarters if not provided
      quarter = `Q${(idx % 4) + 1}`;
    }
    
    // Extract clean article number from regulation_reference
    // Format examples: 
    // - "Article 13: AMLR 2024/1624 (text...)" -> "Article 13"
    // - "AMLR_1: Filename (text...)" -> extract "Article X" from text
    let articleNumber = '';
    if (rec.regulation_reference) {
      // First, try to extract article number from the reference string
      const articleMatch = rec.regulation_reference.match(/Article\s+(\d+)/i);
      if (articleMatch) {
        articleNumber = `Article ${articleMatch[1]}`;
      } else {
        // If no article found, try to extract from label before colon
        const labelMatch = rec.regulation_reference.match(/^([^:]+):/);
        if (labelMatch && labelMatch[1] !== 'AMLR_1') {
          articleNumber = labelMatch[1].trim();
        }
      }
    }
    
    return {
      id: `m${idx}`,
      title: rec.module,
      roleResponsibility: rec.role_reference,
      amlrArticle: articleNumber, // Now contains just "Article 13" or similar
      riskTheme: rec.risk_reference,
      competency: rec.competency_reference,
      confidence: 0.95,
      behaviouralOutcomes: [rec.behavioural_outcome],
      quarter: quarter,
    };
  }) || [];

  // Debug: Log the data
  console.log('Workflow Data:', workflowData);
  console.log('Modules:', modules);
  console.log('Recommendations raw:', workflowData?.recommendations);

  // Group modules by quarter
  const quarterGroups = {
    Q1: modules.filter((m: any) => m.quarter === 'Q1'),
    Q2: modules.filter((m: any) => m.quarter === 'Q2'),
    Q3: modules.filter((m: any) => m.quarter === 'Q3'),
    Q4: modules.filter((m: any) => m.quarter === 'Q4'),
  };

  console.log('Quarter Groups:', quarterGroups);

  const handleReset = () => {
    setWorkflowData(null);
    setError(null);
  };

  return (
    <div className="flex flex-col flex-1 items-center justify-start bg-zinc-50 font-sans dark:bg-black py-8 px-6 min-h-screen">
      <main className="flex flex-1 w-full max-w-5xl flex-col items-stretch gap-8">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Image src="/next.svg" alt="logo" width={80} height={18} className="dark:invert" />
            <h1 className="text-2xl font-semibold">Vidda — Training builder</h1>
          </div>
          {workflowData && (
            <Button variant="outline" onClick={handleReset}>
              Start Over
            </Button>
          )}
        </header>

        {error && (
          <div className="bg-destructive/10 border-l-4 border-destructive text-destructive p-4 rounded-md">
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {!workflowData ? (
          <section className="flex flex-col items-center gap-6 mt-8 w-full max-w-2xl mx-auto">
            <InputSection onProcess={handleProcess} isLoading={isLoading} />

            {/* Saved plans history */}
            <SavedPlansPanel
              refreshTrigger={planRefresh}
              onSelect={(planId) => fetchWorkflowStatus(planId)}
            />
            {/* Loading Stage Indicator */}
            {isLoading && loadingStage && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white dark:bg-zinc-900 rounded-lg p-8 shadow-2xl max-w-md w-full mx-4">
                  <div className="flex flex-col items-center space-y-4">
                    {/* Spinner */}
                    <div className="relative w-16 h-16">
                      <div className="absolute inset-0 border-4 border-blue-200 rounded-full animate-pulse"></div>
                      <div className="absolute inset-0 border-4 border-t-blue-600 rounded-full animate-spin"></div>
                    </div>
                    
                    {/* Stage Text */}
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        {loadingStage}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        This may take 20-30 seconds
                      </p>
                    </div>
                    
                    {/* Progress Steps */}
                    <div className="w-full mt-4 space-y-2">
                      <div className={`flex items-center gap-2 text-sm ${loadingStage.includes('role') ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                        <div className={`w-2 h-2 rounded-full ${loadingStage.includes('role') ? 'bg-blue-600 animate-pulse' : 'bg-gray-300'}`}></div>
                        <span>Analyzing role description</span>
                      </div>
                      <div className={`flex items-center gap-2 text-sm ${loadingStage.includes('regulations') ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                        <div className={`w-2 h-2 rounded-full ${loadingStage.includes('regulations') ? 'bg-blue-600 animate-pulse' : 'bg-gray-300'}`}></div>
                        <span>Searching AMLR regulations</span>
                      </div>
                      <div className={`flex items-center gap-2 text-sm ${loadingStage.includes('requirements') ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                        <div className={`w-2 h-2 rounded-full ${loadingStage.includes('requirements') ? 'bg-blue-600 animate-pulse' : 'bg-gray-300'}`}></div>
                        <span>Extracting compliance requirements</span>
                      </div>
                      <div className={`flex items-center gap-2 text-sm ${loadingStage.includes('training') ? 'text-blue-600 font-medium' : 'text-gray-400'}`}>
                        <div className={`w-2 h-2 rounded-full ${loadingStage.includes('training') ? 'bg-blue-600 animate-pulse' : 'bg-gray-300'}`}></div>
                        <span>Generating quarterly training plan</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>
        ) : (
          <section className="flex flex-col items-center justify-center py-8">
            <div className="w-full max-w-6xl space-y-6">
              {/* Title */}
              <div className="text-center mb-8">
                <h2 className="text-3xl font-bold mb-2">Training Path – Year 1</h2>
                <p className="text-lg text-muted-foreground mb-1">Building knowledge to embedded behaviour</p>
                <p className="text-md font-semibold text-primary">Role: {workflowData.role_data?.role}</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Total modules: {modules.length} | 
                  Q1: {quarterGroups.Q1.length} | 
                  Q2: {quarterGroups.Q2.length} | 
                  Q3: {quarterGroups.Q3.length} | 
                  Q4: {quarterGroups.Q4.length}
                </p>
              </div>

              {/* Quarterly Training Path */}
              <div className="bg-card border rounded-lg p-6 shadow-sm">
                <div className="grid grid-cols-4 gap-4">
                  {/* Q1: Foundation */}
                  <div className="space-y-3">
                    <div className="bg-amber-100 dark:bg-amber-900 rounded-lg p-3 text-center border-b-4 border-amber-300 dark:border-amber-700">
                      <h3 className="font-bold text-base text-foreground">Q1: Foundation</h3>
                      <p className="text-xs mt-1 text-muted-foreground">Months 1-3</p>
                    </div>
                    <ul className="space-y-2 list-none">
                      {quarterGroups.Q1.length > 0 ? (
                        quarterGroups.Q1.map((module: any, idx: number) => (
                          <li key={idx} className="text-sm pl-0">
                            <div className="flex items-start gap-2">
                              <span className="text-primary mt-0.5">•</span>
                              <div className="flex-1">
                                <p className="font-medium leading-tight">
                                  {module.title}
                                  {module.amlrArticle && (
                                    <span className="text-muted-foreground font-normal"> ({module.amlrArticle})</span>
                                  )}
                                </p>
                              </div>
                            </div>
                          </li>
                        ))
                      ) : (
                        <li className="text-sm text-muted-foreground italic">No modules assigned</li>
                      )}
                    </ul>
                  </div>

                  {/* Q2: Application */}
                  <div className="space-y-3">
                    <div className="bg-teal-100 dark:bg-teal-900 rounded-lg p-3 text-center border-b-4 border-teal-300 dark:border-teal-700">
                      <h3 className="font-bold text-base text-foreground">Q2: Application</h3>
                      <p className="text-xs mt-1 text-muted-foreground">Months 4-6</p>
                    </div>
                    <ul className="space-y-2 list-none">
                      {quarterGroups.Q2.length > 0 ? (
                        quarterGroups.Q2.map((module: any, idx: number) => (
                          <li key={idx} className="text-sm pl-0">
                            <div className="flex items-start gap-2">
                              <span className="text-primary mt-0.5">•</span>
                              <div className="flex-1">
                                <p className="font-medium leading-tight">
                                  {module.title}
                                  {module.amlrArticle && (
                                    <span className="text-muted-foreground font-normal"> ({module.amlrArticle})</span>
                                  )}
                                </p>
                              </div>
                            </div>
                          </li>
                        ))
                      ) : (
                        <li className="text-sm text-muted-foreground italic">No modules assigned</li>
                      )}
                    </ul>
                  </div>

                  {/* Q3: Deepening */}
                  <div className="space-y-3">
                    <div className="bg-blue-100 dark:bg-blue-900 rounded-lg p-3 text-center border-b-4 border-blue-300 dark:border-blue-700">
                      <h3 className="font-bold text-base text-foreground">Q3: Deepening</h3>
                      <p className="text-xs mt-1 text-muted-foreground">Months 7-9</p>
                    </div>
                    <ul className="space-y-2 list-none">
                      {quarterGroups.Q3.length > 0 ? (
                        quarterGroups.Q3.map((module: any, idx: number) => (
                          <li key={idx} className="text-sm pl-0">
                            <div className="flex items-start gap-2">
                              <span className="text-primary mt-0.5">•</span>
                              <div className="flex-1">
                                <p className="font-medium leading-tight">
                                  {module.title}
                                  {module.amlrArticle && (
                                    <span className="text-muted-foreground font-normal"> ({module.amlrArticle})</span>
                                  )}
                                </p>
                              </div>
                            </div>
                          </li>
                        ))
                      ) : (
                        <li className="text-sm text-muted-foreground italic">No modules assigned</li>
                      )}
                    </ul>
                  </div>

                  {/* Q4: Embedding */}
                  <div className="space-y-3">
                    <div className="bg-purple-100 dark:bg-purple-900 rounded-lg p-3 text-center border-b-4 border-purple-300 dark:border-purple-700">
                      <h3 className="font-bold text-base text-foreground">Q4: Embedding</h3>
                      <p className="text-xs mt-1 text-muted-foreground">Months 10-12</p>
                    </div>
                    <ul className="space-y-2 list-none">
                      {quarterGroups.Q4.length > 0 ? (
                        quarterGroups.Q4.map((module: any, idx: number) => (
                          <li key={idx} className="text-sm pl-0">
                            <div className="flex items-start gap-2">
                              <span className="text-primary mt-0.5">•</span>
                              <div className="flex-1">
                                <p className="font-medium leading-tight">
                                  {module.title}
                                  {module.amlrArticle && (
                                    <span className="text-muted-foreground font-normal"> ({module.amlrArticle})</span>
                                  )}
                                </p>
                              </div>
                            </div>
                          </li>
                        ))
                      ) : (
                        <li className="text-sm text-muted-foreground italic">No modules assigned</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Plan Quality Scorecard */}
              <PlanScorecard planId={workflowData.training_plan_id} />

              {/* Approval Workflow */}
              <ApprovalWorkflow
                planId={workflowData.training_plan_id}
                onPlanUpdated={() => fetchWorkflowStatus(workflowData.training_plan_id)}
              />
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
