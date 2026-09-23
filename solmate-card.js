const THEMES={electricGold:{name:"Electric Gold",primary:"#FFD700",secondary:"#FFA500",glow:"rgba(255, 215, 0, 0.4)",track:"rgba(255, 215, 0, 0.15)",gradient:["#FFD700","#FF9900","#FFE666","#FFD700"]},cyberEmerald:{name:"Cyber Emerald",primary:"#1AE666",secondary:"#00A64C",glow:"rgba(26, 230, 102, 0.4)",track:"rgba(26, 230, 102, 0.15)",gradient:["#1AE666","#00A64C","#66FF99","#1AE666"]},plasmaCyan:{name:"Plasma Cyan",primary:"#0DD9FF",secondary:"#0073E6",glow:"rgba(13, 217, 255, 0.4)",track:"rgba(13, 217, 255, 0.15)",gradient:["#0DD9FF","#0073E6","#66F2FF","#0DD9FF"]},solarCrimson:{name:"Solar Crimson",primary:"#FF5933",secondary:"#CC2900",glow:"rgba(255, 89, 51, 0.4)",track:"rgba(255, 89, 51, 0.15)",gradient:["#FF5933","#CC2900","#FF8566","#FF5933"]},ultraViolet:{name:"Ultra Violet",primary:"#CC4DFF",secondary:"#8800CC",glow:"rgba(204, 77, 255, 0.4)",track:"rgba(204, 77, 255, 0.15)",gradient:["#CC4DFF","#8800CC","#E699FF","#CC4DFF"]},titaniumMetal:{name:"Titanium Metal",primary:"#E6EBF5",secondary:"#78859B",glow:"rgba(230, 235, 245, 0.3)",track:"rgba(230, 235, 245, 0.15)",gradient:["#E6EBF5","#78859B","#A3B1C6","#E6EBF5"]}},APPEARANCES={glassDark:{bg:"linear-gradient(135deg, rgba(28, 30, 38, 0.85) 0%, rgba(18, 20, 26, 0.95) 100%)",border:"rgba(255, 255, 255, 0.08)",text:"#FFFFFF",textSecondary:"rgba(255, 255, 255, 0.70)",nodeBg:"rgba(255, 255, 255, 0.06)",nodeBorder:"rgba(255, 255, 255, 0.10)",pipeColor:"rgba(255, 255, 255, 0.12)"},obsidianOLED:{bg:"#000000",border:"rgba(255, 255, 255, 0.14)",text:"#FFFFFF",textSecondary:"rgba(255, 255, 255, 0.65)",nodeBg:"rgba(255, 255, 255, 0.05)",nodeBorder:"rgba(255, 255, 255, 0.12)",pipeColor:"rgba(255, 255, 255, 0.12)"},pureLight:{bg:"#FFFFFF",border:"rgba(0, 0, 0, 0.08)",text:"#1C1D21",textSecondary:"#6B7280",nodeBg:"#F3F4F6",nodeBorder:"#E5E7EB",pipeColor:"rgba(0, 0, 0, 0.10)"},warmWhite:{bg:"#FBF9F5",border:"rgba(102, 82, 56, 0.12)",text:"#2B2217",textSecondary:"#6B5E52",nodeBg:"#F4EFE6",nodeBorder:"rgba(102, 82, 56, 0.15)",pipeColor:"rgba(102, 82, 56, 0.15)"}};class SolmateCard extends HTMLElement{constructor(){super(),this.attachShadow({mode:"open"}),this._config={},this._hass=null,this._batteryCapacityKWh=10}setConfig(e){this._config={theme:"electricGold",appearance:"glassDark",title:e.title||null,show_flow:e.show_flow!==!1,show_stats:e.show_stats!==!1,battery_capacity:e.battery_capacity||10,...e},this._batteryCapacityKWh=this._config.battery_capacity,this.render()}set hass(e){this._hass=e,this.updateData()}getCardSize(){return 4}getGridOptions(){return{columns:12,rows:6,min_columns:6,min_rows:4}}formatPower(e){if(e==null||isNaN(e))return"0 W";const o=Math.abs(e);return o>=1e3?`${(o/1e3).toFixed(1)} kW`:`${Math.round(o)} W`}findEntityId(e,o){if(this._config[e])return this._config[e];if(!this._hass)return null;const a=Object.keys(this._hass.states);for(const t of o){const i=a.find(s=>s.startsWith("sensor.solmate_")&&s.endsWith(t));if(i)return i}return null}getTelemetry(){if(!this._hass)return{soc:85,pvPower:2450,battPower:-1800,gridPower:20,loadPower:670,dailyPV:14.8,independenceScore:92,batteryStatus:"Full in 1h 15m",isConnected:!0};const e=(c,p)=>{const l=this.findEntityId(c,p);if(l&&this._hass.states[l]){const f=parseFloat(this._hass.states[l].state);return isNaN(f)?null:f}return null},o=(c,p)=>{const l=this.findEntityId(c,p);return l&&this._hass.states[l]?this._hass.states[l].state:null},a=e("battery_soc",["battery_soc","battery_state_of_charge"])??0,t=e("solar_power",["pv_power","solar_power"])??0,i=e("battery_power",["batt_power","battery_power"])??0,s=e("grid_power",["grid_power"])??0,r=e("load_power",["load_power"])??0,n=e("daily_pv",["daily_pv_yield","daily_solar_yield"])??0,d=e("solar_independence",["solar_independence"])??100,u=o("battery_status",["battery_status"])||this.computeETA(a,i);return{soc:a,pvPower:t,battPower:i,gridPower:s,loadPower:r,dailyPV:n,independenceScore:d,batteryStatus:u,isConnected:!0}}computeETA(e,o){if(e>=99)return"Fully Charged";if(Math.abs(o)<=20)return"Idle";const a=this._batteryCapacityKWh;if(o<-20){const t=(1-e/100)*a*1e3,i=Math.abs(o),s=t/i;if(s<.16)return"Full in < 10m";if(s<1)return`Full in ${Math.round(s*60)}m`;const r=Math.floor(s),n=Math.round((s-r)*60);return n>0?`Full in ${r}h ${n}m`:`Full in ${r}h`}if(o>20){const s=Math.max(0,e/100-.1)*a*1e3/o;if(s<1)return`${Math.max(1,Math.round(s*60))}m left`;const r=Math.floor(s),n=Math.round((s-r)*60);return n>0?`${r}h ${n}m left`:`${r}h left`}return"Idle"}render(){const e=this._config.theme||"electricGold",o=this._config.appearance||"glassDark",a=THEMES[e]||THEMES.electricGold,t=APPEARANCES[o]||APPEARANCES.glassDark,i=this._config.title!==void 0?this._config.title:"Solmate";this.shadowRoot.innerHTML=`
      <style>
        :host {
          display: block;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }
        .solmate-container {
          background: ${t.bg};
          border: 1px solid ${t.border};
          border-radius: 24px;
          padding: 22px 20px;
          box-shadow: 0 12px 36px rgba(0,0,0,0.25);
          color: ${t.text};
          position: relative;
          overflow: hidden;
          box-sizing: border-box;
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }
        .header-title {
          font-size: 14px;
          font-weight: 700;
          letter-spacing: 0.8px;
          text-transform: uppercase;
          color: ${t.textSecondary};
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .header-badge {
          font-size: 11px;
          padding: 3px 8px;
          border-radius: 12px;
          background: ${a.glow};
          color: ${a.primary};
          font-weight: 700;
          letter-spacing: 0.5px;
        }
        
        /* Torus Gauge Area */
        .gauge-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          margin: 10px 0 20px 0;
          position: relative;
        }
        .gauge-wrapper {
          position: relative;
          width: 170px;
          height: 170px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .gauge-svg {
          width: 170px;
          height: 170px;
          transform: rotate(-90deg);
        }
        .gauge-bg-ring {
          fill: none;
          stroke: ${a.track};
          stroke-width: 12;
        }
        .gauge-fill-ring {
          fill: none;
          stroke: url(#themeGrad);
          stroke-width: 12;
          stroke-linecap: round;
          transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1);
          filter: drop-shadow(0 0 6px ${a.glow});
        }
        .gauge-center-content {
          position: absolute;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
        }
        .soc-text {
          font-size: 38px;
          font-weight: 800;
          line-height: 1;
          letter-spacing: -1px;
          color: ${t.text};
        }
        .soc-unit {
          font-size: 22px;
          font-weight: 600;
          opacity: 0.8;
          margin-left: 2px;
        }
        .status-pill {
          margin-top: 6px;
          font-size: 11px;
          font-weight: 700;
          padding: 3px 9px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        .status-charging {
          background: rgba(34, 197, 94, 0.2);
          color: #22C55E;
          border: 1px solid rgba(34, 197, 94, 0.4);
        }
        .status-discharging {
          background: ${a.glow};
          color: ${a.primary};
          border: 1px solid ${a.primary}55;
        }
        .status-idle {
          background: rgba(156, 163, 175, 0.15);
          color: ${t.textSecondary};
          border: 1px solid rgba(156, 163, 175, 0.3);
        }
        .eta-text {
          font-size: 11.5px;
          color: ${t.textSecondary};
          margin-top: 4px;
          font-weight: 500;
        }

        /* 4-Node Energy Flow */
        .flow-section {
          position: relative;
          width: 100%;
          height: 180px;
          margin: 10px 0;
        }
        .flow-canvas-svg {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        .flow-pipe {
          stroke: ${t.pipeColor};
          stroke-width: 3;
          stroke-linecap: round;
        }
        .flow-stream {
          stroke-width: 3;
          stroke-linecap: round;
          stroke-dasharray: 6 8;
          animation: flowDash 1.2s linear infinite;
        }
        .flow-stream.reverse {
          animation: flowDashRev 1.2s linear infinite;
        }
        @keyframes flowDash {
          from { stroke-dashoffset: 28; }
          to { stroke-dashoffset: 0; }
        }
        @keyframes flowDashRev {
          from { stroke-dashoffset: 0; }
          to { stroke-dashoffset: 28; }
        }

        .flow-node {
          position: absolute;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background: ${t.nodeBg};
          border: 1px solid ${t.nodeBorder};
          border-radius: 14px;
          padding: 7px 10px;
          min-width: 66px;
          box-shadow: 0 4px 14px rgba(0,0,0,0.15);
          transform: translate(-50%, -50%);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          transition: transform 0.2s ease;
        }
        .flow-node .node-icon {
          font-size: 16px;
          margin-bottom: 2px;
        }
        .flow-node .node-title {
          font-size: 9px;
          font-weight: 700;
          letter-spacing: 0.6px;
          color: ${t.textSecondary};
          text-transform: uppercase;
        }
        .flow-node .node-value {
          font-size: 12px;
          font-weight: 700;
          color: ${t.text};
          margin-top: 1px;
        }

        /* Center Inverter Node */
        .inverter-hub {
          position: absolute;
          top: 90px;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 40px;
          height: 40px;
          box-sizing: border-box;
          border-radius: 50%;
          background: ${t.cardBackground||t.nodeBg};
          border: 2px solid ${a.primary};
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 0 16px ${a.glow};
          color: ${a.primary};
          z-index: 2;
          user-select: none;
        }
        .inverter-hub svg {
          display: block;
        }

        /* Stats Strip Footer */
        .stats-footer {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
          margin-top: 14px;
          padding-top: 14px;
          border-top: 1px solid ${t.border};
        }
        .stat-card {
          background: ${t.nodeBg};
          border: 1px solid ${t.nodeBorder};
          border-radius: 14px;
          padding: 10px 14px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .stat-label {
          font-size: 11px;
          color: ${t.textSecondary};
          font-weight: 600;
        }
        .stat-val {
          font-size: 14px;
          font-weight: 800;
          color: ${t.text};
        }
        .badge-independence {
          color: ${a.primary};
          font-weight: 800;
        }
      </style>

      <div class="solmate-container">
        <!-- Header -->
        <div class="header">
          <div class="header-title">
            <span>\u26A1\uFE0F</span>
            <span>${i}</span>
          </div>
          <div class="header-badge" id="independenceBadge">--% Solar</div>
        </div>

        <!-- Battery Torus Section -->
        <div class="gauge-section">
          <div class="gauge-wrapper">
            <svg class="gauge-svg" viewBox="0 0 170 170">
              <defs>
                <linearGradient id="themeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="${a.gradient[0]}" />
                  <stop offset="50%" stop-color="${a.gradient[1]}" />
                  <stop offset="100%" stop-color="${a.gradient[2]}" />
                </linearGradient>
              </defs>
              <circle class="gauge-bg-ring" cx="85" cy="85" r="70" />
              <circle id="gaugeFill" class="gauge-fill-ring" cx="85" cy="85" r="70" stroke-dasharray="439.8" stroke-dashoffset="439.8" />
            </svg>
            <div class="gauge-center-content">
              <div class="soc-text"><span id="socVal">--</span><span class="soc-unit">%</span></div>
              <div id="statusPill" class="status-pill status-idle">
                <span id="statusIcon">\u26A1\uFE0F</span>
                <span id="statusText">Connecting</span>
              </div>
              <div class="eta-text" id="etaVal">Calculating...</div>
            </div>
          </div>
        </div>

        <!-- 4-Node Energy Flow Section -->
        ${this._config.show_flow?`
          <div class="flow-section" id="flowSection">
            <svg class="flow-canvas-svg" id="flowSvg">
              <!-- Static connection lines -->
              <line x1="50%" y1="28" x2="50%" y2="50%" class="flow-pipe" />
              <line x1="50%" y1="50%" x2="50%" y2="152" class="flow-pipe" />
              <line x1="18%" y1="50%" x2="50%" y2="50%" class="flow-pipe" />
              <line x1="50%" y1="50%" x2="82%" y2="50%" class="flow-pipe" />

              <!-- Animated flow lines -->
              <line id="streamSolar" x1="50%" y1="28" x2="50%" y2="50%" class="flow-stream" stroke="#FBBF24" style="display:none;" />
              <line id="streamBattery" x1="50%" y1="50%" x2="50%" y2="152" class="flow-stream" stroke="${a.primary}" style="display:none;" />
              <line id="streamGrid" x1="18%" y1="50%" x2="50%" y2="50%" class="flow-stream" stroke="#FB923C" style="display:none;" />
              <line id="streamLoad" x1="50%" y1="50%" x2="82%" y2="50%" class="flow-stream" stroke="#38BDF8" style="display:none;" />
            </svg>

            <!-- Center Inverter Hub -->
            <div class="inverter-hub">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="m8 3-4 4 4 4"/>
                <path d="M4 7h16"/>
                <path d="m16 21 4-4-4-4"/>
                <path d="M20 17H4"/>
              </svg>
            </div>

            <!-- Solar Node (Top) -->
            <div class="flow-node" style="top: 28px; left: 50%;">
              <div class="node-icon">\u2600\uFE0F</div>
              <div class="node-title">Solar</div>
              <div class="node-value" id="valSolar">0 W</div>
            </div>

            <!-- Battery Node (Bottom) -->
            <div class="flow-node" style="top: 152px; left: 50%;">
              <div class="node-icon">\u{1F50B}</div>
              <div class="node-title">Battery</div>
              <div class="node-value" id="valBattery">0 W</div>
            </div>

            <!-- Grid Node (Left) -->
            <div class="flow-node" style="top: 50%; left: 18%;">
              <div class="node-icon">\u{1F5FC}</div>
              <div class="node-title">Grid</div>
              <div class="node-value" id="valGrid">0 W</div>
            </div>

            <!-- Home Load Node (Right) -->
            <div class="flow-node" style="top: 50%; left: 82%;">
              <div class="node-icon">\u{1F3E0}</div>
              <div class="node-title">Home</div>
              <div class="node-value" id="valLoad">0 W</div>
            </div>
          </div>
        `:""}

        <!-- Stats Strip Footer -->
        ${this._config.show_stats?`
          <div class="stats-footer">
            <div class="stat-card">
              <span class="stat-label">Daily Solar</span>
              <span class="stat-val" id="valDailyPV">-- kWh</span>
            </div>
            <div class="stat-card">
              <span class="stat-label">Self-Reliance</span>
              <span class="stat-val badge-independence" id="valIndependence">--%</span>
            </div>
          </div>
        `:""}
      </div>
    `,this.updateData()}updateData(){if(!this.shadowRoot)return;const e=this.getTelemetry(),o=439.82,a=Math.max(0,Math.min(100,e.soc)),t=o-a/100*o,i=this.shadowRoot.getElementById("gaugeFill"),s=this.shadowRoot.getElementById("socVal");i&&(i.style.strokeDashoffset=`${t}`),s&&(s.innerText=`${Math.round(a)}`);const r=this.shadowRoot.getElementById("statusPill"),n=this.shadowRoot.getElementById("statusIcon"),d=this.shadowRoot.getElementById("statusText"),u=this.shadowRoot.getElementById("etaVal");u&&(u.innerText=e.batteryStatus||"Idle"),r&&n&&d&&(e.battPower<-15?(r.className="status-pill status-charging",n.innerText="\u26A1\uFE0F",d.innerText=`+${this.formatPower(e.battPower)}`):e.battPower>15?(r.className="status-pill status-discharging",n.innerText="\u{1F53B}",d.innerText=`-${this.formatPower(e.battPower)}`):(r.className="status-pill status-idle",n.innerText="\u23F8",d.innerText="Idle"));const c=this.shadowRoot.getElementById("valSolar"),p=this.shadowRoot.getElementById("valBattery"),l=this.shadowRoot.getElementById("valGrid"),f=this.shadowRoot.getElementById("valLoad");c&&(c.innerText=this.formatPower(e.pvPower)),p&&(p.innerText=this.formatPower(e.battPower)),l&&(l.innerText=this.formatPower(e.gridPower)),f&&(f.innerText=this.formatPower(e.loadPower));const y=this.shadowRoot.getElementById("streamSolar"),g=this.shadowRoot.getElementById("streamBattery"),h=this.shadowRoot.getElementById("streamGrid"),m=this.shadowRoot.getElementById("streamLoad");y&&(y.style.display=e.pvPower>25?"block":"none"),g&&(e.battPower<-20?(g.style.display="block",g.setAttribute("class","flow-stream")):e.battPower>20?(g.style.display="block",g.setAttribute("class","flow-stream reverse")):g.style.display="none"),h&&(e.gridPower>20?(h.style.display="block",h.setAttribute("class","flow-stream")):e.gridPower<-20?(h.style.display="block",h.setAttribute("class","flow-stream reverse")):h.style.display="none"),m&&(m.style.display=e.loadPower>25?"block":"none");const x=this.shadowRoot.getElementById("valDailyPV"),b=this.shadowRoot.getElementById("valIndependence"),w=this.shadowRoot.getElementById("independenceBadge");x&&(x.innerText=e.dailyPV>0?`${e.dailyPV.toFixed(1)} kWh`:"0 kWh"),b&&(b.innerText=`${e.independenceScore}%`),w&&(w.innerText=`${e.independenceScore}% Solar`)}}customElements.define("solmate-card",SolmateCard),window.customCards=window.customCards||[],window.customCards.push({type:"solmate-card",name:"Solmate Solar Card",description:"Universal real-time solar battery torus gauge and live energy flow visualizer.",preview:!0}),console.info("%c \u26A1\uFE0F SOLMATE CARD \u26A1\uFE0F %c v1.0.0 Loaded ","color: #000000; background: #FFD700; font-weight: bold; border-radius: 4px;","color: #FFFFFF; background: #1C1E26; font-weight: bold; border-radius: 4px;");
