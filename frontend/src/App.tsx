import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { ethers } from 'ethers';

declare global {
    interface Window {
        ethereum: any;
    }
}

// Icons (Simulated with SVG for professional look)
const ActivityIcon = () => (
    <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
);
const SendIcon = () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
    </svg>
);
const ShieldIcon = () => (
    <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
);
const HistoryIcon = () => (
    <svg className="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
);
const PanicIcon = () => (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
);

const App: React.FC = () => {
    const [isTrading, setIsTrading] = useState(false);
    const [walletAddress, setWalletAddress] = useState<string | null>(null);
    const [ethBalance, setEthBalance] = useState<string>('0.00');
    const [messages, setMessages] = useState<{ sender: 'user' | 'agent'; text: string }[]>([
        { sender: 'agent', text: 'Initialize Complete. I am monitoring live feeds for **BTC/USD** and **ETH/USD**. How can I assist with your portfolio?' }
    ]);
    const [inputText, setInputText] = useState('');
    const [portfolioData, setPortfolioData] = useState<any>(null);
    const [tradeHistory, setTradeHistory] = useState<any[]>([]);
    const [marketData, setMarketData] = useState<any[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Dynamic API Configuration
    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch(`${API_BASE}/portfolio/status`);
                const data = await res.json();
                setPortfolioData(data);

                const histRes = await fetch(`${API_BASE}/portfolio/history`);
                const histData = await histRes.json();
                setTradeHistory(histData);

                // Fetch Live Market Data
                const marketRes = await fetch(`${API_BASE}/scan/all`);
                const mData = await marketRes.json();
                setMarketData(mData);
            } catch (e) {
                console.error("Failed to fetch status", e);
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 3000);
        return () => clearInterval(interval);
    }, []);

    const toggleTrading = async () => {
        const endpoint = isTrading ? '/execute/stop' : '/execute/start';
        try {
            await fetch(`${API_BASE}${endpoint}`, { method: 'POST' });
            setIsTrading(!isTrading);
            const msg = !isTrading
                ? "🚀 **Autonomous Strategy Engaged**. Market scanning and risk monitors are live."
                : "🛑 **Safe Halt Executed**. All automated scanning paused.";
            setMessages(prev => [...prev, { sender: 'agent', text: msg }]);
        } catch (e) {
            alert("Error: " + e);
        }
    };

    const panicClose = async () => {
        if (!confirm("⚠️ EMERGENCY: LIQUIDATE ALL POSITIONS? This will immediately close all active trades.")) return;
        try {
            const res = await fetch(`${API_BASE}/portfolio/close_all`, { method: 'POST' });
            const data = await res.json();
            if (isTrading) {
                await fetch(`${API_BASE}/execute/stop`, { method: 'POST' });
                setIsTrading(false);
            }
            setMessages(prev => [...prev, {
                sender: 'agent',
                text: `🔥 **EMERGENCY LIQUIDATION COMPLETE**\n\n- **Positions Closed**: ${data.closed_positions}\n- **Agent Status**: Offline\n\nPortfolio is now 100% Cash/Stable.`
            }]);
            const statusRes = await fetch(`${API_BASE}/portfolio/status`);
            const statusData = await statusRes.json();
            setPortfolioData(statusData);
        } catch (e) {
            alert("Panic failed: " + e);
        }
    };

    const sendMessage = async () => {
        if (!inputText.trim()) return;
        const userMsg = inputText;
        setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
        setInputText('');
        try {
            const res = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userMsg })
            });
            const data = await res.json();
            setMessages(prev => [...prev, { sender: 'agent', text: data.response }]);
        } catch (e) {
            setMessages(prev => [...prev, { sender: 'agent', text: "⚠️ Signal lost. Check backend connection." }]);
        }
    };

    const connectWallet = async () => {
        if (window.ethereum) {
            try {
                const provider = new ethers.BrowserProvider(window.ethereum);
                const signer = await provider.getSigner();
                const address = await signer.getAddress();
                const bal = await provider.getBalance(address);
                setWalletAddress(address);
                setEthBalance(ethers.formatEther(bal));
                setMessages(prev => [...prev, {
                    sender: 'agent',
                    text: `📡 **Wallet Link Established**\n\n- **Auth**: ${address.slice(0, 10)}...\n- **Liquidity**: ${ethers.formatEther(bal).slice(0, 7)} ETH`
                }]);
            } catch (error) {
                console.error("Connection failed", error);
            }
        } else {
            alert("Web3 Provider not found.");
        }
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="min-h-screen bg-[#050810] text-slate-200 font-sans selection:bg-cyan-500/30 selection:text-cyan-200 overflow-x-hidden">
            {/* AMBIENT BACKGROUND */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-cyan-500/10 blur-[120px] rounded-full"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full"></div>
                <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 brightness-50 contrast-150"></div>
            </div>

            {/* HEADER */}
            <header className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#050810]/40 backdrop-blur-xl">
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 h-20 flex items-center justify-between">
                    <div className="flex items-center gap-3 sm:gap-4">
                        <div className="relative">
                            <div className={`w-2.5 h-2.5 sm:w-3 h-3 rounded-full ${isTrading ? 'bg-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.8)]' : 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.5)]'} animate-pulse`}></div>
                        </div>
                        <div className="flex flex-col">
                            <h1 className="text-lg sm:text-xl font-black tracking-tighter text-white uppercase italic leading-none">
                                ANTIGRAVITY <span className="text-cyan-400 not-italic font-medium text-base sm:text-lg ml-1">v2.0</span>
                            </h1>
                            <span className="text-[8px] sm:text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">Autonomous Intelligence</span>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 sm:gap-3">
                        <button
                            onClick={panicClose}
                            className="flex items-center justify-center w-10 h-10 sm:w-auto sm:px-4 sm:py-2 rounded-lg bg-red-500/10 hover:bg-red-500 border border-red-500/20 text-red-500 hover:text-white transition-all duration-300 font-black text-[10px]"
                        >
                            <PanicIcon /> <span className="hidden sm:inline ml-2">TERMINATE</span>
                        </button>

                        <div className="h-8 w-px bg-white/10 mx-1 hidden md:block"></div>

                        {walletAddress ? (
                            <div className="hidden sm:flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
                                <div className="text-right">
                                    <div className="text-[8px] text-slate-500 font-bold uppercase">ETH</div>
                                    <div className="text-xs font-mono text-cyan-400">{parseFloat(ethBalance).toFixed(2)}</div>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={connectWallet}
                                className="hidden sm:block px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all hover:border-cyan-500/50"
                            >
                                Connect
                            </button>
                        )}

                        <button
                            onClick={toggleTrading}
                            className={`flex items-center gap-2 px-4 sm:px-6 py-2 sm:py-2.5 rounded-lg font-black text-[10px] uppercase tracking-widest transition-all duration-500 ${isTrading
                                ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                                : 'bg-cyan-500 text-black hover:bg-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.3)]'
                                }`}
                        >
                            {isTrading ? 'STOP' : 'DEPLOY'}
                        </button>
                    </div>
                </div>
            </header>

            {/* MAIN CONTENT */}
            <main className="pt-28 px-6 max-w-[1600px] mx-auto pb-12">

                {/* METRICS HUD */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <MetricHUD
                        label="CURRENT EQUITY"
                        value={`$${portfolioData?.account?.equity?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`}
                        sub="Real-time Balance"
                        glow="cyan"
                    />
                    <MetricHUD
                        label="DAILY PERFORMANCE"
                        value={`$${portfolioData?.risk_metrics?.daily_pnl?.toFixed(2) || '0.00'}`}
                        trend={portfolioData?.risk_metrics?.daily_pnl >= 0 ? "+UP" : "-DOWN"}
                        glow={portfolioData?.risk_metrics?.daily_pnl >= 0 ? "emerald" : "red"}
                    />
                    <MetricHUD
                        label="ACTIVE POSITIONS"
                        value={portfolioData?.risk_metrics?.open_positions?.toString() || '0'}
                        sub="Scanning Active Trades"
                        glow="blue"
                    />
                    <MetricHUD
                        label="RISK EXPOSURE"
                        value={`${portfolioData?.risk_metrics?.portfolio_exposure_pct?.toFixed(2) || '0.00'}%`}
                        sub="Allocated Capital"
                        glow="purple"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                    {/* LEFT PANEL: TERMINAL MONITOR */}
                    <div className="lg:col-span-8 space-y-6">

                        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl px-4">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-sm font-black text-slate-400 flex items-center gap-3 tracking-[0.2em]">
                                    <ShieldIcon /> RISK PROTOCOLS
                                </h3>
                                <div className="text-[10px] text-emerald-500 font-bold uppercase tracking-widest bg-emerald-500/10 px-2 py-1 rounded">Secured</div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <HUDProgress label="MAX DAILY LOSS" value={portfolioData?.risk_metrics?.daily_loss_pct || 0} max={2} color="red" />
                                <HUDProgress label="CAPITAL DEPLOYMENT" value={portfolioData?.risk_metrics?.portfolio_exposure_pct || 0} max={100} color="cyan" />
                            </div>
                        </div>

                        {/* LIVE FEED OVERHAUL */}
                        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl relative">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-sm font-black text-slate-400 flex items-center gap-3 tracking-[0.2em]">
                                    <ActivityIcon /> MARKET INTELLIGENCE
                                </h3>
                                <div className="flex gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                                    <span className="w-1.5 h-1.5 rounded-full bg-slate-700"></span>
                                    <span className="w-1.5 h-1.5 rounded-full bg-slate-700"></span>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {marketData.length > 0 ? (
                                    marketData.map((asset, idx) => (
                                        <AssetPro
                                            key={idx}
                                            symbol={asset.symbol}
                                            name={asset.symbol === 'BTC' ? 'Bitcoin' : asset.symbol === 'ETH' ? 'Ethereum' : asset.symbol}
                                            price={asset.price}
                                            sentiment={asset.trend === 'Positive' ? 'Bullish' : asset.trend === 'Negative' ? 'Bearish' : 'Neutral'}
                                            change={asset.change}
                                            logic="Neural Analysis"
                                        />
                                    ))
                                ) : (
                                    <div className="col-span-2 text-center py-8 text-slate-600 font-bold">Connecting to Market Feeds...</div>
                                )}
                            </div>
                        </div>

                        {/* RECENT ACTIVITY TABLE */}
                        <div className="bg-[#0f172a]/40 border border-white/5 rounded-3xl p-6 sm:p-8 backdrop-blur-2xl">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-6">
                                <h3 className="text-sm font-black text-slate-400 flex items-center gap-3 tracking-[0.2em]">
                                    <HistoryIcon /> TRANSACTION LOG
                                </h3>
                                <button className="text-[10px] font-bold text-cyan-400 hover:text-cyan-300 uppercase tracking-widest">View Full Audit</button>
                            </div>

                            <div className="overflow-x-auto">
                                <div className="min-w-[500px] sm:min-w-0 space-y-2">
                                    {(() => {
                                        const all = [
                                            ...(portfolioData?.open_trades?.map((t: any) => ({ ...t, status: 'OPEN' })) || []),
                                            ...(tradeHistory?.map((t: any) => ({ ...t, status: 'CLOSED' })) || [])
                                        ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

                                        if (all.length === 0) return <div className="py-12 text-center text-slate-600 font-medium italic text-sm italic">System standby. No trades detected.</div>;

                                        return all.slice(0, 6).map((trade, idx) => (
                                            <div key={idx} className="group grid grid-cols-4 items-center p-4 hover:bg-white/5 rounded-xl border border-transparent hover:border-white/5 transition-all duration-200">
                                                <div className="flex items-center gap-4">
                                                    <div className={`w-1 h-8 rounded-full ${trade.status === 'OPEN' ? 'bg-cyan-500' : trade.pnl >= 0 ? 'bg-emerald-500' : 'bg-red-500'}`}></div>
                                                    <div>
                                                        <div className="text-sm font-black text-white">{trade.symbol}</div>
                                                        <div className="text-[10px] text-slate-500 font-mono italic uppercase tracking-wider">{trade.status}</div>
                                                    </div>
                                                </div>
                                                <div className="text-xs font-mono text-slate-400">
                                                    {new Date(trade.timestamp).toLocaleTimeString()}
                                                </div>
                                                <div className="text-right">
                                                    <div className={`text-xs font-black ${trade.side.toLowerCase() === 'buy' ? 'text-emerald-400' : 'text-cyan-400'}`}>
                                                        {trade.side.toUpperCase()}
                                                    </div>
                                                    <div className="text-[10px] text-slate-500 uppercase font-bold">Execution</div>
                                                </div>
                                                <div className="text-right">
                                                    {trade.status === 'CLOSED' ? (
                                                        <div className={`text-sm font-black ${trade.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                                            {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                                                        </div>
                                                    ) : (
                                                        <div className="text-xs text-cyan-400 font-black animate-pulse">ACTIVE</div>
                                                    )}
                                                    <div className="text-[10px] text-slate-500 font-mono tracking-tighter">PNL %</div>
                                                </div>
                                            </div>
                                        ));
                                    })()}
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* RIGHT PANEL: AI BRAIN */}
                    <div className="lg:col-span-4">
                        <div className="bg-[#0f172a]/60 border border-white/5 rounded-[2rem] flex flex-col h-[500px] lg:h-[740px] shadow-2xl relative overflow-hidden backdrop-blur-3xl ring-1 ring-white/10">
                            {/* BRAIN HEADER */}
                            <div className="p-6 border-b border-white/5 bg-white/5 backdrop-blur-md flex justify-between items-center">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                                        <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></div>
                                    </div>
                                    <div>
                                        <div className="text-xs font-black text-white tracking-widest uppercase">Neural Core</div>
                                        <div className="text-[10px] text-cyan-400/80 font-bold uppercase animate-pulse">Active & Solving</div>
                                    </div>
                                </div>
                                <div className="text-[10px] font-mono text-slate-600 bg-black/40 px-2 py-0.5 rounded border border-white/5">CPU: 4%</div>
                            </div>

                            {/* MESSAGES */}
                            <div
                                ref={scrollRef}
                                className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide"
                            >
                                {messages.map((msg, idx) => (
                                    <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`max-w-[90%] group ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                                            <div className={`px-4 py-3 rounded-2xl text-[13px] leading-relaxed shadow-lg ${msg.sender === 'user'
                                                ? 'bg-cyan-500 text-black font-semibold rounded-tr-none'
                                                : 'bg-white/5 text-slate-200 border border-white/10 rounded-tl-none'
                                                }`}>
                                                <div className="prose prose-invert prose-sm max-w-none">
                                                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                                                </div>
                                            </div>
                                            <div className={`mt-2 text-[8px] font-black uppercase tracking-[0.2em] text-slate-600 px-1`}>
                                                {msg.sender === 'agent' ? 'Brain Response' : 'Operator Message'}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* INPUT LAYER */}
                            <div className="p-6 bg-black/40 border-t border-white/5">
                                <div className="relative group">
                                    <input
                                        type="text"
                                        value={inputText}
                                        onChange={(e) => setInputText(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                        placeholder="Command Interface..."
                                        className="w-full bg-white/5 border border-white/10 rounded-xl pl-5 pr-14 py-4 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 transition-all duration-300"
                                    />
                                    <button
                                        onClick={sendMessage}
                                        className="absolute right-3 top-2.5 p-2 bg-cyan-500 text-black rounded-lg hover:bg-cyan-400 transition-colors shadow-lg active:scale-95 transition-transform"
                                    >
                                        <SendIcon />
                                    </button>
                                </div>
                                <div className="mt-3 text-[9px] text-center text-slate-700 font-bold uppercase tracking-widest">
                                    Secure LLM-Powered Execution Layer
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
};

// --- TERMINAL COMPONENTS ---

const MetricHUD = ({ label, value, trend, sub, glow }: any) => (
    <div className="bg-[#0f172a]/30 border border-white/5 p-6 rounded-3xl backdrop-blur-2xl hover:bg-white/5 transition-all duration-300 group overflow-hidden relative">
        {/* GLOW DECOR */}
        <div className={`absolute -right-4 -top-4 w-12 h-12 rounded-full opacity-10 blur-2xl ${glow === 'cyan' ? 'bg-cyan-400' : glow === 'red' ? 'bg-red-500' : glow === 'emerald' ? 'bg-emerald-500' : 'bg-purple-500'
            }`}></div>

        <div className="text-[10px] text-slate-500 font-black tracking-[.25em] mb-3 uppercase flex items-center justify-between">
            {label}
            {trend && <span className={`font-mono ${glow === 'red' ? 'text-red-400' : 'text-emerald-400'}`}>{trend}</span>}
        </div>
        <div className="text-3xl font-black text-white tracking-tighter mb-1.5 flex items-baseline gap-1">
            {value}
        </div>
        {sub && <div className="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{sub}</div>}
    </div>
);

const AssetPro = ({ symbol, name, price, sentiment, change, logic }: any) => (
    <div className="group flex items-center justify-between p-5 bg-white/3 border border-white/5 rounded-2xl hover:bg-white/5 hover:border-white/10 transition-all duration-300">
        <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-black text-xs border border-white/10 ${symbol === 'BTC' ? 'bg-orange-500/10 text-orange-400' :
                symbol === 'ETH' ? 'bg-blue-500/10 text-blue-400' :
                    symbol === 'SOL' ? 'bg-purple-500/10 text-purple-400' : 'bg-slate-700/20 text-slate-400'
                }`}>
                {symbol}
            </div>
            <div>
                <div className="font-black text-sm text-white flex items-center gap-2">
                    {name} <span className="text-[10px] text-slate-600 font-mono tracking-tighter">CRYPTO</span>
                </div>
                <div className="text-[10px] text-slate-500 uppercase font-black tracking-widest mt-0.5">{logic}</div>
            </div>
        </div>
        <div className="text-right">
            <div className="text-sm font-mono font-bold text-slate-300">{price}</div>
            <div className={`text-[10px] font-black uppercase tracking-widest mt-1 ${sentiment === 'Bullish' ? 'text-emerald-400' : 'text-red-400'}`}>
                {sentiment} {change}
            </div>
        </div>
    </div>
);

const HUDProgress = ({ label, value, max, color }: any) => {
    const pct = Math.min((Math.abs(value) / max) * 100, 100);
    return (
        <div>
            <div className="flex justify-between text-[10px] font-black tracking-widest text-slate-500 mb-2">
                <span>{label}</span>
                <span className="font-mono">{value.toFixed(2)}% / {max}%</span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-1000 ${color === 'red' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' : 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)]'
                        }`}
                    style={{ width: `${pct}%` }}
                ></div>
            </div>
        </div>
    );
};

export default App;
