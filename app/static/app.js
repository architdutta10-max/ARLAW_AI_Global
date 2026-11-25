const $=id=>document.getElementById(id);
const HISTORY_KEY='arlaw-chat-history-v1';
let conversations=[];let activeConversationId=null;let history=[];let sending=false;
try{conversations=JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');if(!Array.isArray(conversations))conversations=[];}catch(e){conversations=[];}
function persistHistory(){try{localStorage.setItem(HISTORY_KEY,JSON.stringify(conversations.slice(0,10)));}catch(e){}}
function renderHistory(){const host=$('historyList');if(!host)return;host.innerHTML='';conversations.slice(0,12).forEach(item=>{const b=document.createElement('button');b.type='button';b.className='history-item'+(item.id===activeConversationId?' active':'');b.textContent=item.title||'New conversation';b.title=item.title||'New conversation';b.onclick=()=>openConversation(item.id);host.append(b);});}
function newConversation(){conversations=conversations.filter(x=>x.messages&&x.messages.length);activeConversationId=(Date.now().toString(36)+Math.random().toString(36).slice(2,7));history=[];conversations.unshift({id:activeConversationId,title:'New conversation',messages:[],updatedAt:Date.now()});persistHistory();renderHistory();}
function saveConversation(){if(!activeConversationId)newConversation();const item=conversations.find(x=>x.id===activeConversationId);if(!item)return;item.messages=history.slice(-30).map(m=>({...m,content:String(m.content||'').slice(0,8000)}));const first=history.find(x=>x.role==='user');if(first)item.title=first.content.slice(0,52)+(first.content.length>52?'…':'');item.updatedAt=Date.now();conversations.sort((a,b)=>(b.updatedAt||0)-(a.updatedAt||0));conversations=conversations.slice(0,10);persistHistory();renderHistory();}
function openConversation(id){const item=conversations.find(x=>x.id===id);if(!item)return;activeConversationId=id;history=Array.isArray(item.messages)?item.messages.slice(-30):[];$('messages').innerHTML='';if(!history.length){showWelcome();}else{for(const m of history)add(m.role,m.content);}renderHistory();show('chat');}
function showWelcome(){$('messages').innerHTML='<div class="welcome"><div class="welcome-mark">A</div><div class="eyebrow">ARLAW AI · LEGAL INTELLIGENCE</div><h1 id="welcomeTitle">What would you like to understand?</h1><p id="welcomeText">Ask clear questions about law, civil disputes, justice, economics, taxation and financial matters.</p><div class="suggest"><button data-prompt="Explain the reasonable classification test under Article 14 of the Constitution of India. Distinguish it from equality before law and equal protection of laws. Cite only retrieved sources."><b>⚖ Constitutional law</b><small>Explore rights and legal principles</small></button><button data-prompt="How can I verify that a legal rule is current and binding? Explain primary and secondary authority."><b>⌕ Verify legal authority</b><small>Check laws, judgments and sources</small></button><button data-prompt="Explain how official sources monitor inflation, food security and energy supply risks."><b>▤ Economy & supply</b><small>Understand indicators and data sources</small></button><button data-prompt="Explain the difference between binding precedent and persuasive authority."><b>⇄ Legal concepts</b><small>Understand complex ideas simply</small></button></div></div>';document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>send(b.dataset.prompt));}
// Theme preference: light by default; the user's choice is persisted locally.
function applyTheme(theme){
  const selected=theme==='dark'?'dark':'light';
  document.documentElement.dataset.theme=selected;
  const dark=selected==='dark';
  const button=$("themeToggle");
  if(button){
    button.setAttribute('aria-label',dark?'Switch to light mode':'Switch to dark mode');
    button.setAttribute('title',dark?'Switch to light mode':'Switch to dark mode');
    button.innerHTML=`<span class="theme-icon" aria-hidden="true">${dark?'☀':'☾'}</span><span class="theme-label">${dark?'Light mode':'Dark mode'}</span>`;
  }
  const meta=document.querySelector('meta[name="theme-color"]');
  if(meta)meta.content=dark?(getComputedStyle(document.documentElement).getPropertyValue('--dark-bg').trim()||'#101b1b'):'#0b827d';
}
let savedTheme='light';
try{savedTheme=localStorage.getItem('arlaw-theme')||'light'}catch(e){}
applyTheme(savedTheme);
$("themeToggle")?.addEventListener('click',()=>{
  const next=document.documentElement.dataset.theme==='dark'?'light':'dark';
  preferences.theme=next;
  applyPreferences();
  savePreferences();
});

// User settings: all preferences are local to this browser and never sent to the API.
const preferenceDefaults={theme:'light',accent:'teal',language:'en',fontSize:'medium',highContrast:false,reduceMotion:false};
const accentPalettes=[
 ['teal','#087f79','#066b67'],['ocean','#087ea4','#075d7a'],['sky','#168acb','#0969a5'],
 ['blue','#315fce','#2347a6'],['royal','#5146c8','#39319a'],['indigo','#5145a8','#39317d'],
 ['violet','#7952c8','#58399c'],['purple','#914fc1','#71399a'],['orchid','#b34caa','#8a3784'],
 ['magenta','#c13d8b','#96306b'],['pink','#d14f82','#a63864'],['rose','#c94b63','#9f344a'],
 ['ruby','#b52d48','#8d2038'],['red','#c43b36','#962b28'],['coral','#d65d45','#a84332'],
 ['orange','#d97726','#a9571b'],['amber','#b98218','#8e6210'],['gold','#a88a24','#806819'],
 ['lime','#718e25','#536b19'],['green','#32834c','#23653a'],['emerald','#16866b','#0e654f'],
 ['mint','#2d927f','#21705f'],['forest','#28634b','#1b4936'],['sage','#718b70','#536a52'],
 ['cyan','#168b99','#0e6975'],['turquoise','#159b9b','#0d7474'],['aqua','#169baf','#0d7183'],
 ['slate','#536b83','#3c5065'],['steel','#557b91','#3c5d70'],['graphite','#59616d','#414852'],
 ['charcoal','#414b57','#2c3540'],['brown','#8b6047','#684632'],['copper','#a96742','#804c30'],
 ['terracotta','#b75c49','#8d4234'],['plum','#75436f','#573252'],['lavender','#8272b8','#62538f']
];
const paletteByName=Object.fromEntries(accentPalettes.map(x=>[x[0],x]));
function setupAccentPicker(){
 const select=$('prefAccent'); if(!select)return;
 select.innerHTML=accentPalettes.map(([name])=>`<option value="${name}">${name[0].toUpperCase()+name.slice(1)}</option>`).join('');
}
function applyAccent(name){
 const palette=paletteByName[name]||paletteByName.teal;
 document.documentElement.style.setProperty('--teal',palette[1]);
 document.documentElement.style.setProperty('--teal-dark',palette[2]);
 document.documentElement.style.setProperty('--accent-soft',`${palette[1]}18`);
 document.documentElement.style.setProperty('--dark-bg',`color-mix(in srgb, ${palette[1]} 13%, #101b1b)`);
 document.documentElement.style.setProperty('--dark-panel',`color-mix(in srgb, ${palette[1]} 17%, #142222)`);
 document.documentElement.style.setProperty('--dark-sidebar',`color-mix(in srgb, ${palette[1]} 62%, #111b20)`);
 document.documentElement.dataset.accent=palette[0];
 if(document.documentElement.dataset.theme==='dark'){
   const meta=document.querySelector('meta[name="theme-color"]');
   if(meta)meta.content=getComputedStyle(document.documentElement).getPropertyValue('--dark-bg').trim()||'#101b1b';
 }
}
function readPreferences(){try{return {...preferenceDefaults,...JSON.parse(localStorage.getItem('arlaw-preferences')||'{}')}}catch(e){return {...preferenceDefaults}}}
let preferences=readPreferences();
setupAccentPicker();
const translations={
 en:{assistant:'Legal research assistant',research:'Research assistant',library:'Knowledge library',newChat:'New chat',workspace:'YOUR WORKSPACE',welcome:'What would you like to understand?',welcomeText:'Ask clear questions about law, civil disputes, justice, economics, taxation and financial matters.',message:'Message ARLAW AI… Include the country, state or court when relevant.',jurisdiction:'Jurisdiction',settings:'Settings',settingsTitle:'User settings',settingsIntro:'Choose how ARLAW AI looks and feels on this device. Your preferences are saved locally in this browser.',appearance:'Appearance',appearanceHint:'Choose light or dark mode',language:'Interface language',languageHint:'Language for menus and controls',fontSize:'Text size',fontSizeHint:'Adjust the interface reading size',contrast:'Higher contrast',contrastHint:'Strengthen borders and text contrast',motion:'Reduce motion',motionHint:'Limit non-essential interface animation',done:'Done',reset:'Reset preferences',note:'Language preference changes the interface labels. Legal answers may still use the language you request in your message.',light:'Light',dark:'Dark',small:'Small',medium:'Default',large:'Large',xlarge:'Extra large',close:'Close settings'},
 hi:{assistant:'कानूनी शोध सहायक',research:'शोध सहायक',library:'ज्ञान पुस्तकालय',newChat:'नई चैट',workspace:'आपका कार्यक्षेत्र',welcome:'आप क्या समझना चाहेंगे?',welcomeText:'कानून, नागरिक विवाद, न्याय, अर्थव्यवस्था, कर और वित्त से जुड़े प्रश्न पूछें।',message:'ARLAW AI को संदेश लिखें… आवश्यकता हो तो देश, राज्य या अदालत बताएं।',jurisdiction:'अधिकार क्षेत्र',settings:'सेटिंग्स',settingsTitle:'उपयोगकर्ता सेटिंग्स',settingsIntro:'इस डिवाइस पर ARLAW AI का रूप और अनुभव चुनें। आपकी पसंद इसी ब्राउज़र में सुरक्षित रहती है।',appearance:'दिखावट',appearanceHint:'लाइट या डार्क मोड चुनें',language:'इंटरफ़ेस भाषा',languageHint:'मेनू और नियंत्रणों की भाषा',fontSize:'अक्षर का आकार',fontSizeHint:'पढ़ने के लिए इंटरफ़ेस का आकार बदलें',contrast:'अधिक कंट्रास्ट',contrastHint:'टेक्स्ट और बॉर्डर को अधिक स्पष्ट करें',motion:'एनिमेशन कम करें',motionHint:'अनावश्यक इंटरफ़ेस एनिमेशन सीमित करें',done:'हो गया',reset:'सेटिंग्स रीसेट करें',note:'भाषा विकल्प इंटरफ़ेस के लेबल बदलता है। कानूनी उत्तर के लिए आप संदेश में अपनी पसंदीदा भाषा बता सकते हैं।',light:'लाइट',dark:'डार्क',small:'छोटा',medium:'सामान्य',large:'बड़ा',xlarge:'बहुत बड़ा',close:'सेटिंग्स बंद करें'},
 bn:{assistant:'আইনি গবেষণা সহায়ক',research:'গবেষণা সহায়ক',library:'জ্ঞানভান্ডার',newChat:'নতুন চ্যাট',workspace:'আপনার কর্মক্ষেত্র',welcome:'আপনি কী জানতে চান?',welcomeText:'আইন, দেওয়ানি বিরোধ, বিচার, অর্থনীতি, কর ও আর্থিক বিষয় নিয়ে প্রশ্ন করুন।',message:'ARLAW AI-কে বার্তা লিখুন… প্রাসঙ্গিক হলে দেশ, রাজ্য বা আদালতের নাম দিন।',jurisdiction:'এখতিয়ার',settings:'সেটিংস',settingsTitle:'ব্যবহারকারীর সেটিংস',settingsIntro:'এই ডিভাইসে ARLAW AI-এর চেহারা ও ব্যবহারের ধরন বেছে নিন। পছন্দগুলি এই ব্রাউজারেই সংরক্ষিত থাকবে।',appearance:'চেহারা',appearanceHint:'লাইট বা ডার্ক মোড বেছে নিন',language:'ইন্টারফেসের ভাষা',languageHint:'মেনু ও নিয়ন্ত্রণের ভাষা',fontSize:'লেখার আকার',fontSizeHint:'পড়ার সুবিধার জন্য ইন্টারফেসের আকার বদলান',contrast:'উচ্চতর কনট্রাস্ট',contrastHint:'লেখা ও সীমানা আরও স্পষ্ট করুন',motion:'অ্যানিমেশন কমান',motionHint:'অপ্রয়োজনীয় ইন্টারফেস অ্যানিমেশন সীমিত করুন',done:'সম্পন্ন',reset:'পছন্দ রিসেট করুন',note:'ভাষার পছন্দ ইন্টারফেসের লেবেল বদলায়। আইনি উত্তরের ভাষা বার্তায় আলাদা করে জানাতে পারেন।',light:'লাইট',dark:'ডার্ক',small:'ছোট',medium:'স্বাভাবিক',large:'বড়',xlarge:'অতি বড়',close:'সেটিংস বন্ধ করুন'}
};
function tr(key){return (translations[preferences.language]||translations.en)[key]||translations.en[key]||key}
function savePreferences(){try{localStorage.setItem('arlaw-preferences',JSON.stringify(preferences));localStorage.setItem('arlaw-theme',preferences.theme)}catch(e){}}
function applyPreferences(){
 applyTheme(preferences.theme);
 applyAccent(preferences.accent);
 if($('prefAccent'))$('prefAccent').value=preferences.accent;
 document.documentElement.dataset.fontSize=preferences.fontSize;
 document.documentElement.classList.toggle('high-contrast',!!preferences.highContrast);
 document.documentElement.classList.toggle('reduce-motion',!!preferences.reduceMotion);
 document.documentElement.lang=preferences.language;
 const keepIcon=(id,key)=>{const el=$(id);if(el&&el.lastChild&&el.lastChild.nodeType===3)el.lastChild.textContent=' '+tr(key)};keepIcon('chatTab','research');keepIcon('sourcesTab','library');
 const jl=$('jurisdiction')?.closest('label');if(jl&&jl.firstChild&&jl.firstChild.nodeType===3)jl.firstChild.textContent=tr('jurisdiction')+' ';
 const map={topTitle:'assistant',workspaceLabel:'workspace',welcomeTitle:'welcome',welcomeText:'welcomeText',prompt:'message',settingsTitle:'settingsTitle',settingsIntro:'settingsIntro',appearanceLabel:'appearance',appearanceHint:'appearanceHint',languageLabel:'language',languageHint:'languageHint',fontSizeLabel:'fontSize',fontSizeHint:'fontSizeHint',contrastLabel:'contrast',contrastHint:'contrastHint',motionLabel:'motion',motionHint:'motionHint',settingsDone:'done',settingsReset:'reset',settingsNote:'note'};
 Object.entries(map).forEach(([id,key])=>{const el=$(id);if(el){if(el.tagName==='TEXTAREA')el.placeholder=tr(key);else el.textContent=tr(key)}});
 const newChat=$('newChat');if(newChat)newChat.innerHTML=`<span>＋</span> ${tr('newChat')}`;
 const settingsOpen=$('settingsOpen');if(settingsOpen)settingsOpen.innerHTML=`⚙ <span>${tr('settings')}</span>`;
 const optionLabels={prefTheme:['light','dark'],prefFontSize:['small','medium','large','xlarge']};Object.entries(optionLabels).forEach(([id,keys])=>{const el=$(id);if(el)Array.from(el.options).forEach((o,i)=>o.textContent=tr(keys[i]))});
 const dialog=$('settingsDialog');if(dialog){$('settingsClose').setAttribute('aria-label',tr('close'));}
 ['prefTheme','prefLanguage','prefFontSize'].forEach((id)=>{const el=$(id);if(el)el.value=preferences[id==='prefTheme'?'theme':id==='prefLanguage'?'language':'fontSize']});
 if($('prefContrast'))$('prefContrast').checked=!!preferences.highContrast;
 if($('prefMotion'))$('prefMotion').checked=!!preferences.reduceMotion;
 const themeToggle=$('themeToggle');if(themeToggle){const dark=preferences.theme==='dark';themeToggle.setAttribute('aria-label',dark?'Switch to light mode':'Switch to dark mode');themeToggle.title=themeToggle.getAttribute('aria-label');themeToggle.innerHTML=`<span class="theme-icon" aria-hidden="true">${dark?'☀':'☾'}</span><span class="theme-label">${tr(dark?'light':'dark')} mode</span>`}
}
function openSettings(){const d=$('settingsDialog');d.classList.remove('hidden');$('settingsClose').focus();}
function closeSettings(){ $('settingsDialog').classList.add('hidden');$('settingsOpen').focus(); }
$('settingsOpen')?.addEventListener('click',openSettings);$('settingsClose')?.addEventListener('click',closeSettings);$('settingsDone')?.addEventListener('click',()=>{savePreferences();applyPreferences();closeSettings()});
$('settingsDialog')?.addEventListener('click',e=>{if(e.target===$('settingsDialog'))closeSettings()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('settingsDialog').classList.contains('hidden'))closeSettings()});
$('prefTheme')?.addEventListener('change',e=>{preferences.theme=e.target.value;applyPreferences();savePreferences()});
$('prefAccent')?.addEventListener('change',e=>{preferences.accent=e.target.value;applyPreferences();savePreferences()});
$('prefLanguage')?.addEventListener('change',e=>{preferences.language=e.target.value;applyPreferences();savePreferences()});
$('prefFontSize')?.addEventListener('change',e=>{preferences.fontSize=e.target.value;applyPreferences();savePreferences()});
$('prefContrast')?.addEventListener('change',e=>{preferences.highContrast=e.target.checked;applyPreferences();savePreferences()});
$('prefMotion')?.addEventListener('change',e=>{preferences.reduceMotion=e.target.checked;applyPreferences();savePreferences()});
$('settingsReset')?.addEventListener('click',()=>{preferences={...preferenceDefaults};savePreferences();applyPreferences()});
applyPreferences();

async function readJson(r){try{return await r.json()}catch(e){return {}}}
function errorText(d,r){const x=d&&d.detail;if(typeof x==='string'&&x)return x;if(Array.isArray(x)&&x.length)return x.map(i=>i&&i.msg?i.msg:String(i)).join('; ');return r&&r.status===429?'Too many requests. Please wait a moment and try again.':'Request failed'+(r&&r.status?' (HTTP '+r.status+')':'')}
function escapeHTML(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function inlineMarkdown(s){return escapeHTML(s).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*(.+?)\*/g,'<em>$1</em>');}
function renderAnswer(raw){
  const lines=String(raw||'').replace(/\r/g,'').split('\n');let out=[],para=[],list=null;
  const flushPara=()=>{if(para.length){out.push('<p>'+para.map(inlineMarkdown).join('<br>')+'</p>');para=[];}};
  const flushList=()=>{if(list){out.push('</'+list+'>');list=null;}};
  for(const line of lines){const t=line.trim();if(!t){flushPara();flushList();continue;}
    const h=t.match(/^(#{1,3})\s+(.+)$/);if(h){flushPara();flushList();const n=h[1].length;out.push('<h'+n+'>'+inlineMarkdown(h[2])+'</h'+n+'>');continue;}
    const bullet=t.match(/^[-*•]\s+(.+)$/);const numbered=t.match(/^\d+[.)]\s+(.+)$/);
    if(bullet||numbered){flushPara();const kind=bullet?'ul':'ol';if(list!==kind){flushList();list=kind;out.push('<'+kind+'>');}out.push('<li>'+inlineMarkdown((bullet||numbered)[1])+'</li>');continue;}
    flushList();para.push(t);
  }
  flushPara();flushList();return out.join('')||'<p></p>';
}
function add(role,text,cites=[]){document.querySelector(".welcome")?.remove();let row=document.createElement("div");row.className="message "+(role==="user"?"user":"assistant");let av=document.createElement("div");av.className="avatar";av.textContent=role==="user"?"YOU":"A";let body=document.createElement("div");body.className="body";body.innerHTML=role==="assistant"?renderAnswer(text):'<p>'+escapeHTML(text).replace(/\n/g,'<br>')+'</p>';row.append(av,body);$("messages").append(row);if(cites.length){let c=document.createElement("div");c.className="citations";c.textContent="Retrieved sources: "+cites.map(x=>`${x.label}: ${x.title} (${x.jurisdiction}, ${x.authority}, ${x.as_of||"date not supplied"}) ${x.url||""}`).join(" · ");$("messages").append(c)}$("messages").scrollTop=$("messages").scrollHeight}
async function send(text){
 if(sending||!text.trim())return;
 if(!activeConversationId)newConversation();
 sending=true;const sendButton=$('chatForm').querySelector('button');sendButton.disabled=true;$('prompt').disabled=true;
 history.push({role:'user',content:text});history=history.slice(-30);add('user',text);saveConversation();
 $('requestStatus').textContent='ARLAW AI is preparing a response…';$('connection').textContent='Generating…';
 const loading=document.createElement('div');loading.className='message assistant loading-message';loading.innerHTML='<div class="avatar">A</div><div class="body"><span class="loading-dots" aria-label="Generating"><i></i><i></i><i></i></span> Researching your question…</div>';$('messages').append(loading);$('messages').scrollTop=$('messages').scrollHeight;
 try{
  let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:history.slice(-30).map(m=>({...m,content:String(m.content||'').slice(0,14000)})),jurisdiction:$('jurisdiction').value})});
  let d=await readJson(r);if(!r.ok)throw Error(errorText(d,r));
  history.push({role:'assistant',content:d.answer});history=history.slice(-30);saveConversation();
  loading.remove();add('assistant',d.answer,d.citations||[]);
  if(d.quality_warning)add('assistant','Reliability warning: '+d.quality_warning);
  const provider=d.model?.provider||'AI';const model=d.model?.model||'connected';$('connection').textContent=d.model_connected?`${provider} · ${model} · ${d.task||'general'}`:'Model unavailable';
 }catch(e){loading.remove();add('assistant','Application error: '+e.message);$('connection').textContent='Request failed';}
 finally{sending=false;sendButton.disabled=false;$('prompt').disabled=false;$('prompt').focus();$('requestStatus').textContent='';}
}
$("chatForm").onsubmit=e=>{e.preventDefault();let t=$("prompt");send(t.value);t.value="";t.style.height=""};$("prompt").oninput=e=>{e.target.style.height="auto";e.target.style.height=Math.min(e.target.scrollHeight,170)+"px"};$("prompt").onkeydown=e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();$("chatForm").requestSubmit()}};
document.querySelectorAll("[data-prompt]").forEach(b=>b.onclick=()=>send(b.dataset.prompt));
$('newChat').onclick=()=>{newConversation();showWelcome();applyPreferences();show('chat');};
renderHistory();
if(conversations.length){openConversation(conversations[0].id);}else{newConversation();}
function show(v){
  $("chatView").classList.toggle("hidden",v!=="chat");
  $("sourcesView").classList.toggle("hidden",v!=="sources");
  $("supportView").classList.toggle("hidden",v!=="support");
  $("chatTab").classList.toggle("active",v==="chat");
  $("sourcesTab").classList.toggle("active",v==="sources");
  $("supportTab").classList.toggle("active",v==="support");
  if(v==="sources"){loadSources();loadRegistry()}
}
$("chatTab").onclick=()=>show("chat");
$("sourcesTab").onclick=()=>show("sources");
$("supportTab").onclick=()=>show("support");
async function loadSources(){let d=await(await fetch("/api/sources")).json();$("sourceList").innerHTML="";if(!d.sources.length){$("sourceList").textContent="No sources indexed yet.";return}d.sources.forEach(s=>{let x=document.createElement("div");x.className="source-row";x.textContent=s.title;let sm=document.createElement("small");sm.textContent=`${s.jurisdiction} · ${s.authority} · ${s.language} · ${s.as_of||"date not supplied"} · ${s.source_url||"URL not supplied"}`;x.append(sm);$("sourceList").append(x)})}
async function loadRegistry(){let d=await(await fetch("/api/registry")).json();$("registryNotice").textContent=d.notice;$("registryList").innerHTML="";d.sources.forEach(s=>{let x=document.createElement("div");x.className="source-row";let a=document.createElement("a");a.href=s.url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=s.name+" ↗";let sm=document.createElement("small");sm.textContent=`${s.jurisdiction} · ${s.type} · ${s.authority}`;x.append(a,sm);$("registryList").append(x)})}
$("uploadForm").onsubmit=async e=>{e.preventDefault();$("uploadStatus").textContent="Indexing…";try{let r=await fetch("/api/documents",{method:"POST",body:new FormData(e.target)});let d=await readJson(r);if(!r.ok)throw Error(errorText(d,r));$("uploadStatus").textContent=`Indexed ${d.chunks} chunks.`;e.target.reset();loadSources()}catch(err){$("uploadStatus").textContent=err.message}};
async function init(){try{let d=await(await fetch("/api/jurisdictions")).json();for(const g of d.groups){let a=document.createElement("optgroup");a.label=g.name;g.items.forEach(j=>{if($("jurisdiction").querySelector(`option[value="${j.code}"]`))return;let o=document.createElement("option");o.value=j.code;o.textContent=j.name;a.append(o)});$("jurisdiction").append(a);let uploadGroup=a.cloneNode(true);for(const option of [...uploadGroup.querySelectorAll("option")])if($("uploadJurisdiction").querySelector(`option[value="${option.value}"]`))option.remove();$("uploadJurisdiction").append(uploadGroup)}/* India is the default because this release is India-focused; users can explicitly select GLOBAL or another jurisdiction. */$("jurisdiction").value="IN";$("uploadJurisdiction").value="IN"}catch(e){$("connection").textContent="Could not load jurisdiction list"}}
init();fetch("/api/health/model").then(r=>r.json()).then(d=>{$("connection").textContent=`AI providers: ${(d.providers||[]).join(", ")||"none configured"}${d.multi_model_review?" · peer review on":""}`}).catch(()=>{$("connection").textContent="Backend ready"});
