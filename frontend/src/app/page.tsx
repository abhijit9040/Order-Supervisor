"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function Home() {
  const [supervisors, setSupervisors] = useState<any[]>([]);
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [supervisorsRes, runsRes] = await Promise.all([
        fetch("/api/supervisors"),
        fetch("/api/runs")
      ]);
      
      // If supervisor endpoint fails (e.g. 404 because none exists), let's create a default one
      let sups = [];
      if (supervisorsRes.ok) {
        sups = await supervisorsRes.json();
      }
      
      if (sups.length === 0) {
        // Create default supervisor
        const createRes = await fetch("/api/supervisors", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: "E-commerce Order Supervisor",
            base_instruction: "Monitor the order lifecycle. Intervene when payment, shipment, customer communication, or fulfillment issues require attention.",
            available_actions: [
              "message_fulfillment_team",
              "message_payments_team",
              "message_logistics_team",
              "message_customer",
              "create_internal_note"
            ]
          })
        });
        if (createRes.ok) {
          const newSup = await createRes.json();
          sups = [newSup];
        }
      }
      
      setSupervisors(sups);
      
      if (runsRes.ok) {
        setRuns(await runsRes.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const createRun = async () => {
    const orderId = `ORDER-${Math.floor(1000 + Math.random() * 9000)}`;
    try {
      const res = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: orderId,
          order_context: { items: ["item_1"] }
        })
      });
      if (res.ok) {
        fetchData();
      } else {
        const errText = await res.text();
        alert(`Failed to create run: ${res.status} ${errText}`);
      }
    } catch (e: any) {
      alert(`Network error: ${e.message}`);
      console.error(e);
    }
  };

  return (
    <main className="p-8 max-w-6xl mx-auto min-h-screen animate-fade-in">
      <div className="flex justify-between items-center mb-10">
        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
          Order Supervisor
        </h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-slate-200">Workflow Runs</h2>
            <button 
              onClick={createRun}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white px-6 py-2.5 rounded-lg shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all font-medium border border-blue-400/30"
            >
              + Create Run
            </button>
          </div>
          
          {loading ? (
            <div className="glass-panel rounded-xl p-8 text-center text-slate-400">Loading runs...</div>
          ) : (
            <div className="space-y-4">
              {runs.map(run => (
                <div key={run.id} className="glass-panel glass-panel-hover p-5 rounded-xl flex items-center justify-between group">
                  <div className="flex flex-col">
                    <Link href={`/runs/${run.workflow_id}`} className="text-xl font-semibold text-blue-400 hover:text-blue-300 transition-colors">
                      {run.order_id}
                    </Link>
                    <span className="text-sm text-slate-400 mt-1 font-mono">{run.workflow_id}</span>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className={`text-xs font-bold px-3 py-1.5 rounded-full uppercase tracking-wider ${
                      run.status === 'AWAKE' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                      run.status === 'SLEEPING' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                      run.status === 'COMPLETED' ? 'bg-green-500/20 text-green-300 border border-green-500/30' :
                      'bg-slate-700/50 text-slate-300 border border-slate-600'
                    }`}>
                      {run.status}
                    </span>
                    <Link href={`/runs/${run.workflow_id}`} className="text-xs text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                      View Details &rarr;
                    </Link>
                  </div>
                </div>
              ))}
              {runs.length === 0 && (
                <div className="glass-panel rounded-xl p-12 flex flex-col items-center justify-center text-slate-400 text-center border-dashed">
                  <p className="text-lg mb-2">No active runs.</p>
                  <p className="text-sm opacity-70">Click &quot;+ Create Run&quot; to start a new order workflow.</p>
                </div>
              )}
            </div>
          )}
        </div>
        
        <div>
          <h2 className="text-2xl font-semibold mb-6 text-slate-200">AI Configuration</h2>
          <div className="space-y-6">
            {supervisors.slice(0, 1).map(sup => (
              <div key={sup.id} className="glass-panel p-6 rounded-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
                
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  {sup.name}
                </h3>
                
                <div className="mt-4 bg-obsidian/50 rounded-lg p-4 border border-slate-700/50">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">System Prompt</h4>
                  <p className="text-sm text-slate-300 leading-relaxed">{sup.base_instruction}</p>
                </div>
                
                <div className="mt-6">
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Available Tools</h4>
                  <div className="flex flex-wrap gap-2">
                    {sup.available_actions.map((act: string) => (
                      <span key={act} className="text-xs bg-slate-800/80 border border-slate-700 text-slate-300 px-2.5 py-1.5 rounded-md font-mono">
                        {act}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
