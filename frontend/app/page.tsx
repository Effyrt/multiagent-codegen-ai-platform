'use client';

import { useState } from 'react';

const API_URL = typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
  ? 'https://codegen-backend-428108273170.us-central1.run.app'
  : 'http://localhost:8080';

interface Agent {
  id: string;
  name: string;
  icon: string;
  status: 'idle' | 'working' | 'completed';
  progress: number;
}

export default function Home() {
  const [description, setDescription] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [agents, setAgents] = useState<Agent[]>([
    { id: 'requirements', name: 'Requirements Analyzer', icon: '📋', status: 'idle', progress: 0 },
    { id: 'programmer', name: 'Code Generator', icon: '⚡', status: 'idle', progress: 0 },
    { id: 'test_designer', name: 'Test Designer', icon: '🧪', status: 'idle', progress: 0 },
    { id: 'test_executor', name: 'Test Executor', icon: '🎯', status: 'idle', progress: 0 },
    { id: 'documentation', name: 'Documentation', icon: '📚', status: 'idle', progress: 0 },
  ]);

  const updateAgent = (id: string, status: 'working' | 'completed', progress: number) => {
    setAgents(prev => prev.map(a => 
      a.id === id ? { ...a, status, progress } : a
    ));
  };

  const generate = async () => {
    if (!description.trim()) {
      console.log('❌ No description provided');
      return;
    }
    
    console.log('🟢 Generate function called');
    console.log('🟢 API_URL:', API_URL);
    console.log('🟢 Description:', description);
    console.log('🟢 Language:', language);
    
    setLoading(true);
    setResult(null);
    setAgents(prev => prev.map(a => ({ ...a, status: 'idle', progress: 0 })));
    
    try {
      console.log('🚀 Starting generation with API:', API_URL);
      
      // Start generation
      const res = await fetch(`${API_URL}/api/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, language })
      });
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      
      const data = await res.json();
      const genId = data.generation_id;
      
      console.log('✅ Generation ID:', genId);
      
      // Simulate agent progress
      const agentSequence = ['requirements', 'programmer', 'test_designer', 'test_executor', 'documentation'];
      let currentAgentIndex = 0;
      
      // Poll for result
      for (let i = 0; i < 60; i++) {
        await new Promise(r => setTimeout(r, 1000));
        
        // Update agent progress
        if (currentAgentIndex < agentSequence.length) {
          const currentAgent = agentSequence[currentAgentIndex];
          const progress = Math.min(100, (i % 6) * 20);
          
          if (progress >= 100) {
            updateAgent(currentAgent, 'completed', 100);
            currentAgentIndex++;
            if (currentAgentIndex < agentSequence.length) {
              updateAgent(agentSequence[currentAgentIndex], 'working', 0);
            }
          } else {
            updateAgent(currentAgent, 'working', progress);
          }
        }
        
        const statusRes = await fetch(`${API_URL}/api/v1/status/${genId}`);
        const status = await statusRes.json();
        console.log('Status response:', status);
        
        if (status.status === 'completed') {
          console.log('Parsing result...');
          // Mark all agents complete
          agentSequence.forEach(id => updateAgent(id, 'completed', 100));
          const resultData = status.result.value
          ? JSON.parse(status.result.value) 
          : status.result;
          console.log('Parsed result:', resultData); 
          setResult(resultData);
          console.log('✅ Generation completed!');
          break;
        }
        if (status.status === 'failed') {
          throw new Error(status.error || 'Generation failed');
        }
      }
    } catch (err: any) {
      console.error('❌ Error:', err);
      alert('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <div style={{maxWidth: '1400px', margin: '0 auto'}}>
        <div style={{textAlign: 'center', marginBottom: '50px'}}>
          <h1 style={{
            fontSize: '64px',
            fontWeight: '800',
            color: 'white',
            marginBottom: '12px',
            textShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }}>
            ⚡ CodeGen AI
          </h1>
          <p style={{fontSize: '20px', color: 'rgba(255,255,255,0.9)'}}>
            Enterprise Multi-Agent Code Generation Platform
          </p>
          <div style={{marginTop: '16px', display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap'}}>
            <span style={{background: 'rgba(255,255,255,0.2)', padding: '6px 16px', borderRadius: '20px', color: 'white', fontSize: '14px', backdropFilter: 'blur(10px)'}}>🤖 5 AI Agents</span>
            <span style={{background: 'rgba(255,255,255,0.2)', padding: '6px 16px', borderRadius: '20px', color: 'white', fontSize: '14px', backdropFilter: 'blur(10px)'}}>🔍 RAG-Enhanced</span>
            <span style={{background: 'rgba(255,255,255,0.2)', padding: '6px 16px', borderRadius: '20px', color: 'white', fontSize: '14px', backdropFilter: 'blur(10px)'}}>☁️ Cloud Deployed</span>
          </div>
        </div>

        <div style={{display: 'grid', gridTemplateColumns: '1fr 400px', gap: '30px'}}>
          <div style={{background: 'white', padding: '40px', borderRadius: '20px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)'}}>
            <label style={{display: 'block', marginBottom: '12px', fontWeight: '700', fontSize: '18px', color: '#1f2937'}}>
              What do you want to build?
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{width: '100%', height: '160px', padding: '16px', fontSize: '16px', border: '2px solid #e5e7eb', borderRadius: '12px', marginBottom: '20px', resize: 'vertical', fontFamily: 'inherit'}}
              placeholder="Example: Create a FastAPI endpoint for user authentication with JWT tokens and password hashing"
            />
            
            <div style={{display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '24px'}}>
              <label style={{fontWeight: '600', color: '#4b5563'}}>Language:</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)} style={{padding: '12px 20px', fontSize: '16px', borderRadius: '10px', border: '2px solid #e5e7eb', cursor: 'pointer', fontWeight: '500'}}>
                <option value="python">🐍 Python</option>
                <option value="javascript">⚡ JavaScript</option>
              </select>
            </div>
            
            <button
              onClick={generate}
              disabled={loading || !description.trim()}
              style={{width: '100%', padding: '18px', fontSize: '20px', fontWeight: '700', background: loading ? 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white', border: 'none', borderRadius: '12px', cursor: loading ? 'not-allowed' : 'pointer', transition: 'transform 0.2s', boxShadow: '0 10px 30px rgba(102, 126, 234, 0.4)'}}
              onMouseEnter={(e) => !loading && (e.currentTarget.style.transform = 'translateY(-2px)')}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              {loading ? '⏳ Agents Working...' : '🚀 Generate Code'}
            </button>
          </div>

          <div style={{background: 'rgba(255,255,255,0.95)', padding: '30px', borderRadius: '20px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', backdropFilter: 'blur(10px)'}}>
            <h3 style={{fontSize: '20px', fontWeight: '700', marginBottom: '24px', color: '#1f2937'}}>🤖 Agent Pipeline</h3>
            
            {agents.map((agent) => (
              <div key={agent.id} style={{marginBottom: '20px'}}>
                <div style={{display: 'flex', alignItems: 'center', marginBottom: '8px'}}>
                  <span style={{fontSize: '24px', marginRight: '12px'}}>{agent.icon}</span>
                  <div style={{flex: 1}}>
                    <div style={{fontSize: '14px', fontWeight: '600', color: agent.status === 'completed' ? '#059669' : agent.status === 'working' ? '#2563eb' : '#6b7280'}}>
                      {agent.name}
                    </div>
                    <div style={{fontSize: '12px', color: '#9ca3af'}}>
                      {agent.status === 'completed' ? '✅ Complete' : agent.status === 'working' ? '⚡ Working...' : 'Waiting...'}
                    </div>
                  </div>
                  {agent.status === 'completed' && <span style={{fontSize: '20px'}}>✅</span>}
                </div>
                
                <div style={{height: '6px', background: '#e5e7eb', borderRadius: '10px', overflow: 'hidden'}}>
                  <div style={{height: '100%', width: `${agent.progress}%`, background: agent.status === 'completed' ? 'linear-gradient(90deg, #059669, #10b981)' : 'linear-gradient(90deg, #2563eb, #3b82f6)', transition: 'width 0.3s ease'}} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {result && (
          <div style={{marginTop: '40px', background: 'white', padding: '40px', borderRadius: '20px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)'}}>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px', marginBottom: '40px'}}>
              <div style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '24px', borderRadius: '16px', color: 'white'}}>
                <div style={{fontSize: '14px', opacity: 0.9, marginBottom: '8px'}}>Quality Score</div>
                <div style={{fontSize: '36px', fontWeight: '800'}}>{result.quality_score?.toFixed(1)}/10</div>
                {result.quality_assessment && <div style={{fontSize: '12px', opacity: 0.8, marginTop: '8px'}}>Confidence: {(result.confidence * 100).toFixed(0)}%</div>}
              </div>
              
              <div style={{background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', padding: '24px', borderRadius: '16px', color: 'white'}}>
                <div style={{fontSize: '14px', opacity: 0.9, marginBottom: '8px'}}>Duration</div>
                <div style={{fontSize: '36px', fontWeight: '800'}}>{result.duration?.toFixed(1)}s</div>
                <div style={{fontSize: '12px', opacity: 0.8, marginTop: '8px'}}>Tokens: {result.tokens_used?.toLocaleString()}</div>
              </div>
              
              <div style={{background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', padding: '24px', borderRadius: '16px', color: 'white'}}>
                <div style={{fontSize: '14px', opacity: 0.9, marginBottom: '8px'}}>Cost</div>
                <div style={{fontSize: '36px', fontWeight: '800'}}>${result.cost?.toFixed(4)}</div>
                <div style={{fontSize: '12px', opacity: 0.8, marginTop: '8px'}}>{result.rag_examples_used || 0} RAG examples</div>
              </div>
              
              {result.validation && (
                <div style={{background: result.validation.is_valid ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' : 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', padding: '24px', borderRadius: '16px', color: 'white'}}>
                  <div style={{fontSize: '14px', opacity: 0.9, marginBottom: '8px'}}>Security</div>
                  <div style={{fontSize: '36px', fontWeight: '800'}}>{result.validation.security_flags?.length === 0 ? '✅' : '⚠️'}</div>
                  <div style={{fontSize: '12px', opacity: 0.8, marginTop: '8px'}}>{result.validation.security_flags?.length === 0 ? 'No issues' : `${result.validation.security_flags.length} flags`}</div>
                </div>
              )}
            </div>
            
            {result.quality_assessment?.breakdown && (
              <div style={{background: '#f9fafb', padding: '24px', borderRadius: '16px', marginBottom: '30px'}}>
                <h3 style={{fontSize: '18px', fontWeight: '700', marginBottom: '20px', color: '#1f2937'}}>📊 Quality Breakdown</h3>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px'}}>
                  {Object.entries(result.quality_assessment.breakdown).map(([key, value]: [string, any]) => (
                    <div key={key} style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                      <div style={{flex: 1}}>
                        <div style={{fontSize: '12px', color: '#6b7280', textTransform: 'capitalize'}}>{key.replace('_', ' ')}</div>
                        <div style={{fontSize: '18px', fontWeight: '700', color: '#1f2937'}}>{value.toFixed(1)}/10</div>
                      </div>
                      <div style={{width: '40px', height: '40px', borderRadius: '50%', background: value >= 8 ? '#10b981' : value >= 6 ? '#f59e0b' : '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: '700'}}>
                        {value >= 8 ? '✓' : value >= 6 ? '○' : '✗'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div style={{marginBottom: '30px'}}>
              <h3 style={{fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '12px'}}>
                <span style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px'}}>📝</span>
                Generated Code
              </h3>
              <pre style={{background: '#1e293b', color: '#e2e8f0', padding: '24px', borderRadius: '12px', overflow: 'auto', fontSize: '14px', lineHeight: '1.6', boxShadow: '0 10px 30px rgba(0,0,0,0.2)'}}>
                <code>{result.code}</code>
              </pre>
            </div>
            
            <div style={{marginBottom: '30px'}}>
              <h3 style={{fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '12px'}}>
                <span style={{background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px'}}>🧪</span>
                Test Cases
              </h3>
              <pre style={{background: '#f8fafc', padding: '24px', borderRadius: '12px', overflow: 'auto', border: '2px solid #e2e8f0', fontSize: '14px', lineHeight: '1.6'}}>
                <code>{result.tests}</code>
              </pre>
            </div>
            
            <div>
              <h3 style={{fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#1f2937', display: 'flex', alignItems: 'center', gap: '12px'}}>
                <span style={{background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', width: '40px', height: '40px', borderRadius: '10px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px'}}>📚</span>
                Documentation
              </h3>
              <pre style={{background: '#f8fafc', padding: '24px', borderRadius: '12px', overflow: 'auto', border: '2px solid #e2e8f0', fontSize: '14px', lineHeight: '1.6', whiteSpace: 'pre-wrap'}}>
                <code>{result.documentation}</code>
              </pre>
            </div>
          </div>
        )}
        
        <div style={{marginTop: '50px', textAlign: 'center', color: 'rgba(255,255,255,0.8)', fontSize: '14px'}}>
          <p>Powered by OpenAI GPT-4 | Deployed on Google Cloud Run & Vercel</p>
          <p style={{marginTop: '8px'}}>Pinecone RAG • Upstash Redis • BigQuery Analytics • Enterprise Guardrails</p>
        </div>
      </div>
    </div>
  );
}
