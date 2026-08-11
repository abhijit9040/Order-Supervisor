"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

export default function RunDetails() {
  const params = useParams();
  const id = params.id as string;
  
  const [run, setRun] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [instruction, setInstruction] = useState("");

  const [isSubmittingInstruction, setIsSubmittingInstruction] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [id]);

  const fetchData = async () => {
    try {
      const [runRes, actRes] = await Promise.all([
        fetch(`/api/runs/${id}`),
        fetch(`/api/runs/${id}/activities`)
      ]);
      
      if (runRes.ok) setRun(await runRes.json());
      if (actRes.ok) setActivities(await actRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const sendEvent = async (eventType: string, message: string) => {
    await fetch(`/api/runs/${id}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event_type: eventType, message })
    });
    fetchData();
  };

  const sendInstruction = async () => {
    if (!instruction || isSubmittingInstruction) return;
    setIsSubmittingInstruction(true);
    try {
      await fetch(`/api/runs/${id}/instructions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instruction })
      });
      setInstruction("");
      await fetchData();
    } finally {
      setIsSubmittingInstruction(false);
    }
  };

  const controlWorkflow = async (action: string) => {
    await fetch(`/api/runs/${id}/${action}`, { method: "POST" });
    fetchData();
  };

  if (loading && !run) return <div className="p-8">Loading...</div>;
  if (!run) return <div className="p-8">Run not found.</div>;

  const isTerminal = run.status === 'COMPLETED' || run.status === 'TERMINATED';

  return (
    <main className="p-4 md:p-8 max-w-7xl mx-auto min-h-screen animate-fade-in">
      <Link href="/" className="text-slate-400 hover:text-white transition-colors mb-6 inline-flex items-center gap-2 text-sm font-medium">
        &larr; Back to Dashboard
      </Link>
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Column: Timeline & Details */}
        <div className="lg:col-span-8 space-y-6">
          
          <div className="glass-panel p-6 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white">{run.order_id}</h1>
              <p className="text-sm text-slate-400 font-mono mt-1 flex items-center gap-2">
                ID: {run.workflow_id}
              </p>
            </div>
            
            <div className={`px-4 py-2 rounded-lg font-bold tracking-widest text-sm flex items-center gap-2 border shadow-lg ${
              run.status === 'AWAKE' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/50 shadow-yellow-500/10' :
              run.status === 'SLEEPING' ? 'bg-blue-500/10 text-blue-400 border-blue-500/50 shadow-blue-500/10' :
              run.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400 border-green-500/50 shadow-green-500/10' :
              run.status === 'PAUSED' ? 'bg-orange-500/10 text-orange-400 border-orange-500/50 shadow-orange-500/10' :
              'bg-slate-800 text-slate-400 border-slate-600'
            }`}>
              {(run.status === 'AWAKE' || run.status === 'SLEEPING') && (
                <span className={`w-2 h-2 rounded-full ${run.status === 'AWAKE' ? 'bg-yellow-400 animate-pulse' : 'bg-blue-400'}`}></span>
              )}
              {run.status}
            </div>
          </div>

          {run.final_summary && (
            <div className="glass-panel border-green-500/30 p-6 rounded-xl bg-green-500/5 animate-slide-up">
              <h2 className="text-xl font-bold text-green-400 mb-4 flex items-center gap-2">
                <span className="text-2xl">✓</span> Workflow Completed
              </h2>
              <div className="space-y-4">
                <div className="bg-obsidian/50 p-4 rounded-lg border border-green-500/20">
                  <h3 className="text-xs font-bold text-green-500/70 uppercase tracking-widest mb-1">Final Summary</h3>
                  <p className="text-slate-200">{run.final_summary}</p>
                </div>
                {run.final_learnings && (
                  <div className="bg-obsidian/50 p-4 rounded-lg border border-green-500/20">
                    <h3 className="text-xs font-bold text-green-500/70 uppercase tracking-widest mb-1">Key Learnings</h3>
                    <p className="text-slate-200">{run.final_learnings}</p>
                  </div>
                )}
                {run.final_feedback && (
                  <div className="bg-obsidian/50 p-4 rounded-lg border border-green-500/20">
                    <h3 className="text-xs font-bold text-green-500/70 uppercase tracking-widest mb-1">Recommendations</h3>
                    <p className="text-slate-200">{run.final_feedback}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="glass-panel p-6 rounded-xl">
            <h2 className="text-xl font-semibold mb-6 text-white border-b border-slate-700/50 pb-4">Activity Timeline</h2>
            
            <div className="relative pl-6 space-y-8 before:absolute before:inset-0 before:ml-[1.4rem] before:h-full before:w-0.5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
              {activities.length === 0 && <p className="text-slate-500 text-center italic">Awaiting events...</p>}
              
              {activities.map((act, idx) => (
                <div key={act.id} className="relative animate-slide-up" style={{animationDelay: `${idx * 0.05}s`}}>
                  <div className={`absolute -left-[1.8rem] w-4 h-4 rounded-full border-2 border-obsidian z-10 ${
                    act.type === 'event' ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.6)]' :
                    act.type === 'action' ? 'bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.6)]' :
                    act.type === 'instruction' ? 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.6)]' : 
                    'bg-slate-500'
                  }`}></div>
                  
                  <div className="bg-obsidian/60 border border-slate-700/50 p-4 rounded-lg shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <span className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded ${
                        act.type === 'event' ? 'text-blue-400 bg-blue-500/10' :
                        act.type === 'action' ? 'text-purple-400 bg-purple-500/10' :
                        act.type === 'instruction' ? 'text-yellow-400 bg-yellow-500/10' : 
                        'text-slate-400 bg-slate-500/10'
                      }`}>
                        {act.type}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">{new Date(act.created_at).toLocaleTimeString()}</span>
                    </div>
                    <pre className="text-sm mt-3 text-slate-300 font-mono whitespace-pre-wrap overflow-x-auto">
                      {JSON.stringify(act.data, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Controls & Simulator */}
        <div className="lg:col-span-4 space-y-6">
          
          <div className="glass-panel p-0 rounded-xl overflow-hidden border border-slate-700 shadow-2xl">
            <div className="bg-slate-900 px-4 py-2 flex items-center gap-2 border-b border-slate-800">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
                <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
              </div>
              <span className="text-xs text-slate-400 font-mono ml-2">agent_memory.json</span>
            </div>
            <div className="p-4 bg-obsidian-light/50 h-64 overflow-y-auto">
              <pre className="text-sm font-mono text-emerald-400 whitespace-pre-wrap">
                {run.memory_summary ? JSON.stringify(run.memory_summary, null, 2) : "// No memory established yet."}
              </pre>
            </div>
          </div>

          <div className={`glass-panel p-5 rounded-xl transition-opacity ${isTerminal ? 'opacity-50 pointer-events-none' : ''}`}>
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Event Simulator</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-xs text-slate-500 mb-2 font-semibold">ORDER</h3>
                <button disabled={isTerminal} onClick={() => sendEvent('order_created', 'Order was created')} className="w-full text-left px-3 py-2 text-sm bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded transition-colors text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed">
                  ⚡ Order Created
                </button>
              </div>
              
              <div>
                <h3 className="text-xs text-slate-500 mb-2 font-semibold">PAYMENT</h3>
                <div className="grid grid-cols-2 gap-2">
                  <button disabled={isTerminal} onClick={() => sendEvent('payment_confirmed', 'Payment successful')} className="px-3 py-2 text-xs bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded transition-colors text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed">Confirmed</button>
                  <button disabled={isTerminal} onClick={() => sendEvent('payment_failed', 'Payment failed')} className="px-3 py-2 text-xs bg-red-950/30 hover:bg-red-900/40 border border-red-900/50 rounded transition-colors text-red-300 disabled:opacity-50 disabled:cursor-not-allowed">Failed</button>
                </div>
              </div>

              <div>
                <h3 className="text-xs text-slate-500 mb-2 font-semibold">SHIPPING</h3>
                <div className="space-y-2">
                  <button disabled={isTerminal} onClick={() => sendEvent('shipment_created', 'Label created')} className="w-full text-left px-3 py-2 text-sm bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded transition-colors text-slate-200 disabled:opacity-50 disabled:cursor-not-allowed">
                    📦 Shipment Created
                  </button>
                  <button disabled={isTerminal} onClick={() => sendEvent('shipment_delayed', 'Delayed by 2 days')} className="w-full text-left px-3 py-2 text-sm bg-orange-950/30 hover:bg-orange-900/40 border border-orange-900/50 rounded transition-colors text-orange-300 disabled:opacity-50 disabled:cursor-not-allowed">
                    ⚠️ Shipment Delayed
                  </button>
                  <button disabled={isTerminal} onClick={() => sendEvent('delivered', 'Successfully delivered')} className="w-full text-left px-3 py-2 text-sm bg-emerald-950/30 hover:bg-emerald-900/40 border border-emerald-900/50 rounded transition-colors text-emerald-300 disabled:opacity-50 disabled:cursor-not-allowed">
                    ✅ Delivered (Terminal)
                  </button>
                </div>
              </div>

              <div>
                <h3 className="text-xs text-slate-500 mb-2 font-semibold">CUSTOMER</h3>
                <div className="grid grid-cols-2 gap-2">
                  <button disabled={isTerminal} onClick={() => sendEvent('customer_message_received', 'Where is my order?')} className="px-3 py-2 text-xs bg-blue-950/30 hover:bg-blue-900/40 border border-blue-900/50 rounded transition-colors text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed">Message</button>
                  <button disabled={isTerminal} onClick={() => sendEvent('refund_requested', 'Requested refund')} className="px-3 py-2 text-xs bg-pink-950/30 hover:bg-pink-900/40 border border-pink-900/50 rounded transition-colors text-pink-300 disabled:opacity-50 disabled:cursor-not-allowed">Refund</button>
                </div>
              </div>
            </div>
          </div>

          <div className={`glass-panel p-5 rounded-xl transition-opacity ${isTerminal ? 'opacity-50 pointer-events-none' : ''}`}>
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-3">Live Instruction</h2>
            <textarea 
              disabled={isTerminal || isSubmittingInstruction}
              className="w-full bg-slate-900/50 border border-slate-700 focus:border-purple-500/50 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-600 outline-none transition-colors resize-none disabled:opacity-50 disabled:cursor-not-allowed" 
              rows={3} 
              placeholder="E.g. If shipment is delayed, prioritize immediate escalation."
              value={instruction}
              onChange={e => setInstruction(e.target.value)}
            />
            <button 
              disabled={isTerminal || isSubmittingInstruction || !instruction.trim()}
              onClick={sendInstruction}
              className="w-full mt-2 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded-lg text-sm font-medium border border-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmittingInstruction ? 'Injecting...' : 'Inject Instruction'}
            </button>
          </div>

          <div className={`glass-panel p-5 rounded-xl transition-opacity ${isTerminal ? 'opacity-50 pointer-events-none' : ''}`}>
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-3">Workflow Controls</h2>
            <div className="flex gap-2">
              <button disabled={isTerminal} onClick={() => controlWorkflow('interrupt')} className="flex-1 bg-slate-800 hover:bg-yellow-900/30 hover:text-yellow-400 text-slate-400 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:border-yellow-700/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed">PAUSE</button>
              <button disabled={isTerminal} onClick={() => controlWorkflow('resume')} className="flex-1 bg-slate-800 hover:bg-blue-900/30 hover:text-blue-400 text-slate-400 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:border-blue-700/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed">RESUME</button>
              <button disabled={isTerminal} onClick={() => controlWorkflow('terminate')} className="flex-1 bg-slate-800 hover:bg-red-900/30 hover:text-red-400 text-slate-400 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:border-red-700/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed">KILL</button>
            </div>
          </div>

        </div>
      </div>
    </main>
  );
}
