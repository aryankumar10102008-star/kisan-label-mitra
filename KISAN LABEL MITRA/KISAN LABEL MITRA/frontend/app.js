const translations = {
  hi: {
    appName:"लेबल पढ़ो", tagline:"दवा का लेबल आसान भाषा में", langGroup:"भाषा चुनें",
    takePhoto:"लेबल की फोटो लें", cameraHint:"कैमरा खोलें", chooseGallery:"गैलरी से चुनें",
    photoReady:"फोटो तैयार है", changePhoto:"फोटो बदलें", cropLabel:"आपकी फसल का नाम",
    cropPlaceholder:"जैसे: कपास, धान, टमाटर", sprayDateLabel:"छिड़काव की तारीख",
    readLabel:"लेबल पढ़ें", needPhoto:"पहले लेबल की फोटो लें",
    loadingTitle:"लेबल पढ़ा जा रहा है…", loadingBody:"थोड़ा इंतज़ार करें। हम लेबल के हर शब्द को ध्यान से पढ़ रहे हैं।",
    sample:"नमूना", toxicityHeading:"ज़हर का स्तर", cropCheck:"फसल जाँच",
    listed:"लेबल पर लिखी है", notListed:"लेबल पर नहीं लिखी", unclear:"साफ़ नहीं",
    listedBody:c=>`“${c}” इस लेबल पर लिखी फसलों में है।`,
    notListedBody:c=>`“${c}” इस लेबल पर नहीं लिखी है। इस फसल पर इसका इस्तेमाल न करें।`,
    unclearBody:"फसल का नाम नहीं दिया गया या लेबल पर साफ़ नहीं है।",
    harvestHeading:"सुरक्षित कटाई की तारीख", harvestFrom:"इस तारीख से पहले कटाई न करें",
    waitDays:n=>`छिड़काव के बाद ${n} दिन रुकें`, noSprayDate:"छिड़काव की तारीख डालें, तब हम कटाई की तारीख बताएँगे।",
    labelSays:"लेबल पर लिखा है", meaning:"इसका मतलब", listen:"सुनें", stop:"रोकें",
    newLabel:"नया लेबल पढ़ें", errorTitle:"लेबल पढ़ नहीं पाए",
    errorBody:"फोटो धुंधली हो सकती है। लेबल को रोशनी में रखकर, पास से दोबारा फोटो लें।",
    retry:"फिर से कोशिश करें", goHome:"शुरुआत पर जाएँ",
    footer:"यह लेबल पर छपी बात समझाता है। छिड़काव से पहले कृषि अधिकारी से पूछें।",
    demoWarning:"यह केवल नमूना डेटा है। इसका उपयोग छिड़काव या कटाई के फैसले के लिए न करें।"
  },
  en: {
    appName:"Label Reader", tagline:"Pesticide labels in simple words", langGroup:"Choose language",
    takePhoto:"Take photo of label", cameraHint:"Opens camera", chooseGallery:"Choose from gallery",
    photoReady:"Photo is ready", changePhoto:"Change photo", cropLabel:"Your crop name",
    cropPlaceholder:"e.g. Cotton, Paddy, Tomato", sprayDateLabel:"Spray date",
    readLabel:"Read label", needPhoto:"Take a photo of the label first",
    loadingTitle:"Reading the label…", loadingBody:"Please wait. We are reading every word on the label carefully.",
    sample:"Sample", toxicityHeading:"Poison level", cropCheck:"Crop check",
    listed:"Listed on label", notListed:"Not listed", unclear:"Unclear",
    listedBody:c=>`“${c}” is one of the crops printed on this label.`,
    notListedBody:c=>`“${c}” is not printed on this label. Do not use it on this crop.`,
    unclearBody:"No crop name was given, or the label is not clear.",
    harvestHeading:"Safe harvest date", harvestFrom:"Do not harvest before this date",
    waitDays:n=>`Wait ${n} days after spraying`, noSprayDate:"Enter the spray date and we will show the harvest date.",
    labelSays:"Label says", meaning:"What it means", listen:"Listen", stop:"Stop",
    newLabel:"Read a new label", errorTitle:"Could not read the label",
    errorBody:"The photo may be blurry. Hold the label in good light and take a closer photo.",
    retry:"Try again", goHome:"Back to start",
    footer:"This explains what is printed. Ask your agriculture officer before spraying.",
    demoWarning:"This is demonstration data only. Do not use it to make spraying or harvesting decisions."
  }
};

const samples = [
  {product:"KisanGuard 20% EC (Chlorpyrifos)",toxicity:"yellow",crops:[{en:"Cotton",hi:"कपास"},{en:"Paddy",hi:"धान"},{en:"Rice",hi:"चावल"}],waitingDays:21,lines:[
    {original:"Dose: 2 ml per litre of water",explain:{hi:"एक लीटर पानी में 2 मिली दवा मिलाएँ। एक टंकी (15 लीटर) में 30 मिली।",en:"Mix 2 ml of medicine in 1 litre of water. For one 15-litre tank, use 30 ml."}},
    {original:"Waiting period: 21 days before harvest",explain:{hi:"छिड़काव के बाद 21 दिन तक फसल न काटें।",en:"Do not harvest the crop for 21 days after spraying."}},
    {original:"Do not spray against the wind. Toxic to fish and bees.",explain:{hi:"हवा की उल्टी दिशा में छिड़काव न करें। तालाब और मधुमक्खियों से दूर रखें।",en:"Do not spray facing the wind. Keep away from ponds and bees."}}
  ]},
  {product:"Fasal Rakshak 75% WP (Mancozeb)",toxicity:"blue",crops:[{en:"Potato",hi:"आलू"},{en:"Tomato",hi:"टमाटर"}],waitingDays:7,lines:[
    {original:"Dose: 2.5 g per litre of water",explain:{hi:"एक लीटर पानी में 2.5 ग्राम पाउडर घोलें।",en:"Dissolve 2.5 grams of powder in 1 litre of water."}},
    {original:"Waiting period: 7 days",explain:{hi:"छिड़काव के 7 दिन बाद ही फसल तोड़ें।",en:"Pick the crop only 7 days after spraying."}}
  ]},
  {product:"Shakti 36% SL (Monocrotophos)",toxicity:"red",crops:[{en:"Cotton",hi:"कपास"}],waitingDays:15,lines:[
    {original:"POISON. Keep out of reach of children.",explain:{hi:"ज़हर है। बच्चों की पहुँच से दूर, ताले में रखें।",en:"This is poison. Lock it away from children."}},
    {original:"Waiting period: 15 days",explain:{hi:"छिड़काव के बाद 15 दिन तक फसल न काटें।",en:"Do not harvest for 15 days after spraying."}}
  ]},
  {product:"Neem Kavach 0.03% EC (Azadirachtin)",toxicity:"green",crops:[{en:"Brinjal",hi:"बैंगन"},{en:"Okra",hi:"भिंडी"},{en:"Cabbage",hi:"पत्ता गोभी"}],waitingDays:3,lines:[
    {original:"Dose: 5 ml per litre of water",explain:{hi:"एक लीटर पानी में 5 मिली दवा मिलाएँ।",en:"Mix 5 ml in 1 litre of water."}},
    {original:"Waiting period: 3 days",explain:{hi:"छिड़काव के 3 दिन बाद फसल तोड़ सकते हैं।",en:"You can pick the crop 3 days after spraying."}}
  ]}
];

const $ = id => document.getElementById(id);
let lang = "hi", photoUrl = null, sampleIndex = 0, currentResult = null, speaking = false;
const screens = ["home-screen","loading-screen","result-screen","error-screen"];

function showScreen(id) {
  screens.forEach(screen => $(screen).classList.toggle("hidden", screen !== id));
  $("main-content").scrollTo({top:0, behavior:"instant"});
}
function setText(id, value) { $(id).textContent = value; }
function updateLanguage() {
  const t = translations[lang];
  document.documentElement.lang = lang;
  $("language-group").setAttribute("aria-label", t.langGroup);
  setText("app-name",t.appName); setText("app-tagline",t.tagline);
  setText("camera-title",photoUrl?t.changePhoto:t.takePhoto); setText("camera-hint",t.cameraHint);
  setText("choose-gallery",t.chooseGallery); setText("photo-ready",t.photoReady);
  setText("crop-label",t.cropLabel); $("crop-input").placeholder=t.cropPlaceholder;
  setText("spray-date-label",t.sprayDateLabel); setText("read-label",t.readLabel);
  setText("need-photo",t.needPhoto); setText("loading-title",t.loadingTitle); setText("loading-body",t.loadingBody);
  setText("toxicity-heading",t.toxicityHeading); setText("sample-label",t.sample);
  setText("crop-check",t.cropCheck); setText("harvest-heading",t.harvestHeading);
  setText("listen-label",speaking?t.stop:t.listen); setText("new-label",t.newLabel);
  setText("error-title",t.errorTitle); setText("error-body",t.errorBody);
  setText("retry-label",t.retry); setText("go-home",t.goHome); setText("footer-text",t.footer);
  setText("demo-warning-text",t.demoWarning);
  document.querySelectorAll(".language-button").forEach(btn=>{
    const active=btn.dataset.lang===lang; btn.classList.toggle("active",active); btn.setAttribute("aria-pressed",String(active));
  });
  if (currentResult) renderResult(currentResult);
}
function selectPhoto(file) {
  if (!file) return;
  if (!file.type.startsWith("image/")) return;
  if (photoUrl) URL.revokeObjectURL(photoUrl);
  photoUrl=URL.createObjectURL(file);
  $("preview-image").src=photoUrl;
  $("photo-preview").classList.remove("hidden");
  $("read-button").disabled=false;
  $("need-photo").classList.add("hidden");
  setText("camera-title",translations[lang].changePhoto);
}
function startRead() {
  if (!photoUrl) return;
  stopSpeech();
  showScreen("loading-screen");
  window.setTimeout(()=>{
    currentResult=samples[sampleIndex % samples.length];
    sampleIndex++;
    renderResult(currentResult);
    showScreen("result-screen");
  },2500);
}
function renderResult(result) {
  const t=translations[lang];
  const toxicity = {
    red:{name:{hi:"लाल – बहुत ज़्यादा ज़हरीला",en:"Red – Extremely toxic"},meaning:{hi:"बहुत खतरनाक। दस्ताने, मास्क और पूरे कपड़े पहनें। बच्चों और पशुओं से दूर रखें।",en:"Very dangerous. Wear gloves, mask and full clothes. Keep away from children and animals."}},
    yellow:{name:{hi:"पीला – काफ़ी ज़हरीला",en:"Yellow – Highly toxic"},meaning:{hi:"खतरनाक। दस्ताने और मास्क पहनें। छिड़काव के बाद हाथ-मुँह साबुन से धोएँ।",en:"Dangerous. Wear gloves and mask. Wash hands and face with soap after spraying."}},
    blue:{name:{hi:"नीला – मध्यम ज़हरीला",en:"Blue – Moderately toxic"},meaning:{hi:"सावधानी रखें। त्वचा और आँखों को बचाएँ। खाने-पीने की चीज़ों से दूर रखें।",en:"Be careful. Protect skin and eyes. Keep away from food and water."}},
    green:{name:{hi:"हरा – कम ज़हरीला",en:"Green – Slightly toxic"},meaning:{hi:"कम खतरा, फिर भी सावधानी ज़रूरी। छिड़काव के बाद हाथ धोएँ।",en:"Low danger, but still be careful. Wash hands after spraying."}}
  }[result.toxicity];
  $("toxicity-card").className="toxicity-card "+result.toxicity;
  setText("toxicity-name",toxicity.name[lang]); setText("toxicity-meaning",toxicity.meaning[lang]); setText("product-name",result.product);
  const crop=$("crop-input").value.trim();
  const match=result.crops.some(c=>c.en.toLowerCase()===crop.toLowerCase() || c.hi===crop);
  const status=!crop?"unclear":match?"listed":"not-listed";
  $("crop-card").className="info-card crop-card "+status;
  const statusText=status==="listed"?t.listed:status==="not-listed"?t.notListed:t.unclear;
  setText("crop-status",statusText);
  setText("crop-status-icon",status==="listed"?"✓":status==="not-listed"?"✕":"?");
  setText("crop-message",status==="listed"?t.listedBody(crop):status==="not-listed"?t.notListedBody(crop):t.unclearBody);
  $("crop-list").innerHTML="";
  result.crops.forEach(c=>{const li=document.createElement("li");li.textContent=c[lang];$("crop-list").appendChild(li);});
  const sprayDate=$("spray-date").value;
  if(sprayDate){
    const [y,m,d]=sprayDate.split("-").map(Number);
    const date=new Date(y,m-1,d+result.waitingDays);
    setText("harvest-date",new Intl.DateTimeFormat(lang==="hi"?"hi-IN":"en-IN",{weekday:"long",day:"numeric",month:"long",year:"numeric"}).format(date));
    setText("harvest-note",t.harvestFrom);
  } else {
    setText("harvest-date",t.noSprayDate); setText("harvest-note","");
  }
  setText("wait-days",t.waitDays(result.waitingDays));
  $("label-lines").innerHTML="";
  result.lines.forEach(line=>{
    const wrap=document.createElement("div"); wrap.className="label-line";
    const original=document.createElement("div"); original.className="label-original";
    const originalTitle=document.createElement("p"); originalTitle.className="eyebrow"; originalTitle.textContent=t.labelSays;
    const originalText=document.createElement("p"); originalText.textContent=line.original;
    const explanation=document.createElement("div"); explanation.className="label-explanation";
    const explanationTitle=document.createElement("p"); explanationTitle.className="eyebrow"; explanationTitle.textContent=t.meaning;
    const explanationText=document.createElement("p"); explanationText.textContent=line.explain[lang];
    original.append(originalTitle,originalText); explanation.append(explanationTitle,explanationText);
    wrap.append(original,explanation); $("label-lines").appendChild(wrap);
  });
}
function stopSpeech() {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  speaking=false; setText("listen-label",translations[lang].listen); setText("listen-icon","🔊");
}
function toggleSpeech() {
  if (!("speechSynthesis" in window)) { alert(lang==="hi"?"इस ब्राउज़र में आवाज़ की सुविधा उपलब्ध नहीं है।":"Speech is not available in this browser."); return; }
  if(speaking){stopSpeech();return;}
  const t=translations[lang], r=currentResult;
  const textToRead=[
    $("toxicity-name").textContent,$("toxicity-meaning").textContent,
    `${t.cropCheck}: ${$("crop-status").textContent}. ${$("crop-message").textContent}`,
    `${t.harvestHeading}: ${$("harvest-date").textContent}. ${$("wait-days").textContent}`,
    ...r.lines.map(line=>line.explain[lang]),t.footer,t.demoWarning
  ].join(" ");
  const utterance=new SpeechSynthesisUtterance(textToRead);
  utterance.lang=lang==="hi"?"hi-IN":"en-IN"; utterance.rate=.9;
  const voice=speechSynthesis.getVoices().find(v=>v.lang.toLowerCase().startsWith(lang));
  if(voice) utterance.voice=voice;
  utterance.onend=stopSpeech; utterance.onerror=stopSpeech;
  speechSynthesis.cancel(); speechSynthesis.speak(utterance);
  speaking=true; setText("listen-label",t.stop); setText("listen-icon","■");
}

$("camera-button").addEventListener("click",()=>$("camera-input").click());
$("gallery-button").addEventListener("click",()=>$("gallery-input").click());
["camera-input","gallery-input"].forEach(id=>$(id).addEventListener("change",e=>selectPhoto(e.target.files[0])));
$("read-button").addEventListener("click",startRead);
$("new-label-button").addEventListener("click",()=>{stopSpeech();showScreen("home-screen");});
$("listen-button").addEventListener("click",toggleSpeech);
$("retry-button").addEventListener("click",startRead);
$("home-button").addEventListener("click",()=>{stopSpeech();showScreen("home-screen");});
document.querySelectorAll(".language-button").forEach(btn=>btn.addEventListener("click",()=>{lang=btn.dataset.lang;updateLanguage();}));
window.addEventListener("beforeunload",()=>{if(photoUrl)URL.revokeObjectURL(photoUrl);stopSpeech();});
updateLanguage();
