const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
let currentUser = null;
let selectedSlot = "8:00 PM - 9:00 PM";
let selectedDate = new Date().toISOString().slice(0,10);
let pendingBookingId = null;
let adminTab = "overview";

async function api(path, options={}) {
  const opts = {...options, headers: {"Content-Type":"application/json", ...(options.headers||{})}};
  const response = await fetch(path, opts);
  const data = await response.json().catch(()=>({success:false,message:"Unexpected server response."}));
  if (!response.ok || data.success === false) throw new Error(data.message || "Request failed.");
  return data;
}
function toast(message, error=false) {
  const node = document.createElement("div");
  node.className = "toast" + (error ? " error" : "");
  node.textContent = message;
  $("#toastWrap").appendChild(node);
  setTimeout(()=>node.remove(), 3800);
}
function esc(value="") {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function openModal(html) {
  $("#modalContent").innerHTML = html;
  $("#modalBackdrop").classList.remove("hidden");
  document.body.style.overflow="hidden";
}
function closeModal() {
  $("#modalBackdrop").classList.add("hidden");
  document.body.style.overflow="";
}
function field(label,name,type="text",placeholder="",required=true,value="") {
  return `<div class="field"><label for="${name}">${label}</label><input id="${name}" name="${name}" type="${type}" placeholder="${placeholder}" value="${esc(value)}" ${required?"required":""} ${type==="date"?`min="${new Date().toISOString().slice(0,10)}"`:""}></div>`;
}
function modalHead(kicker,title,desc="") {
  return `<div class="modal-kicker">${kicker}</div><h2 id="modalTitle">${title}</h2>${desc?`<p>${desc}</p>`:""}`;
}
function authModal(mode="login") {
  const register = mode==="register";
  openModal(`${modalHead("WELCOME TO FANCLUB",register?"JOIN THE CLUB.":"GOOD TO SEE YOU.",register?"Create an account to book grounds and connect with local players.":"Log in to manage your bookings and football community.")}<form id="authForm" class="form-grid">
    ${register?field("FULL NAME","name","text","Your full name"):""}
    ${register?field("PHONE NUMBER","phone","tel","10-digit mobile number"):""}
    ${field("EMAIL ADDRESS","email","email","you@example.com")}
    ${field("PASSWORD","password","password",register?"At least 8 characters":"Your password")}
    ${register?field("CONFIRM PASSWORD","confirm","password","Repeat password"):""}
    <p id="formMessage" class="form-message"></p><button class="btn full-btn" type="submit">${register?"CREATE ACCOUNT":"LOGIN"} <span>↗</span></button>
  </form><p class="switch-auth">${register?"Already a member?":"New to FanClub?"} <button id="switchAuth">${register?"Log in":"Create an account"}</button></p>`);
  $("#switchAuth").onclick=()=>authModal(register?"login":"register");
  $("#authForm").onsubmit=async e=>{
    e.preventDefault(); const f=new FormData(e.currentTarget); const msg=$("#formMessage"); msg.textContent="";
    if(register && f.get("password")!==f.get("confirm")){msg.textContent="Passwords do not match.";return;}
    const btn=$("button[type=submit]",e.currentTarget); btn.disabled=true;btn.textContent="PLEASE WAIT…";
    try{
      const data=await api(register?"/api/register":"/api/login",{method:"POST",body:JSON.stringify({name:f.get("name"),phone:f.get("phone"),email:f.get("email"),password:f.get("password")})});
      currentUser=data.user; closeModal(); updateNav(); toast(data.message); await refreshPublic();
      if(window.FANCLUB_CONFIG?.openAdmin && currentUser.role==="admin") adminModal();
    }catch(err){msg.textContent=err.message;toast(err.message,true);}
    finally{btn.disabled=false;btn.textContent=register?"CREATE ACCOUNT ↗":"LOGIN ↗";}
  };
}
function bookingModal(slot=selectedSlot) {
  if(!currentUser){toast("Please log in or create an account to book.");authModal("login");return;}
  selectedSlot=slot;
  openModal(`${modalHead("BOOK YOUR PITCH","LOCK IN YOUR SLOT.","Ryan Vibgyor KPC Empyrean · Kharghar · ₹200 per 60-minute slot")}
    <form id="bookingForm" class="form-grid">
      ${field("FULL NAME","bookName","text","Name on the booking",true,currentUser.name)}
      ${field("PHONE NUMBER","bookPhone","tel","Contact number",true,currentUser.phone)}
      <div class="form-two">${field("DATE","bookDate","date","",true,selectedDate)}<div class="field"><label for="bookSlot">TIME SLOT</label><select id="bookSlot" required><option ${selectedSlot=== "8:00 PM - 9:00 PM"?"selected":""}>8:00 PM - 9:00 PM</option><option ${selectedSlot=== "9:00 PM - 10:00 PM"?"selected":""}>9:00 PM - 10:00 PM</option></select></div></div>
      <div class="summary-box"><div class="summary-row"><span>Venue</span><strong>Ryan Vibgyor KPC Empyrean</strong></div><div class="summary-row"><span>Location</span><strong>Kharghar</strong></div><div class="summary-row"><span>Total</span><strong>₹200</strong></div></div>
      <p id="formMessage" class="form-message"></p><button class="btn full-btn" type="submit">RESERVE & CONTINUE <span>↗</span></button>
    </form>`);
  $("#bookDate").min=new Date().toISOString().slice(0,10);
  $("#bookingForm").onsubmit=async e=>{
    e.preventDefault(); const f=new FormData(e.currentTarget); const btn=$("button[type=submit]",e.currentTarget);btn.disabled=true;
    try{
      const data=await api("/api/bookings",{method:"POST",body:JSON.stringify({name:f.get("bookName"),phone:f.get("bookPhone"),date:f.get("bookDate"),time_slot:$("#bookSlot").value})});
      pendingBookingId=data.booking_id;selectedDate=f.get("bookDate");selectedSlot=$("#bookSlot").value; paymentModal(data.booking_id);
    }catch(err){$("#formMessage").textContent=err.message;toast(err.message,true);}
    finally{btn.disabled=false;}
  };
}
function paymentModal(id) {
  openModal(`${modalHead("STEP 2 / PAYMENT","DEMO CHECKOUT.","This is a college-project simulation. No real money will be charged.")}
    <div class="summary-box"><div class="summary-row"><span>Booking ID</span><strong>#FC-${id}</strong></div><div class="summary-row"><span>Venue</span><strong>Ryan Vibgyor KPC Empyrean</strong></div><div class="summary-row"><span>Date & time</span><strong>${esc(selectedDate)} · ${esc(selectedSlot)}</strong></div><div class="summary-row"><span>Amount</span><strong>₹200</strong></div></div>
    <form id="paymentForm" class="form-grid"><div class="field"><label for="payMethod">PAYMENT METHOD</label><select id="payMethod"><option value="UPI">UPI (simulated)</option><option value="Card">Card (simulated — no card details needed)</option><option value="Cash at Venue">Cash at venue</option></select></div><p class="muted-small">For safety, this demo does not collect or store card numbers, CVV, or bank credentials.</p><p id="formMessage" class="form-message"></p><button class="btn full-btn" type="submit">CONFIRM DEMO PAYMENT · ₹200 <span>↗</span></button></form>`);
  $("#paymentForm").onsubmit=async e=>{
    e.preventDefault();const btn=$("button[type=submit]",e.currentTarget);btn.disabled=true;btn.textContent="PROCESSING…";
    try{const result=await api("/api/payment",{method:"POST",body:JSON.stringify({booking_id:id,method:$("#payMethod").value})});
      openModal(`${modalHead("YOU'RE ALL SET","BOOKING CONFIRMED.","${result.message}")}<div class="summary-box"><div class="summary-row"><span>Booking ID</span><strong>#FC-${id}</strong></div><div class="summary-row"><span>Venue</span><strong>Ryan Vibgyor KPC Empyrean</strong></div><div class="summary-row"><span>Date</span><strong>${esc(selectedDate)}</strong></div><div class="summary-row"><span>Time</span><strong>${esc(selectedSlot)}</strong></div><div class="summary-row"><span>Amount</span><strong>₹200</strong></div><div class="summary-row"><span>Payment status</span><strong>${esc(result.payment_status)}</strong></div></div><button class="btn full-btn" id="viewBookings">VIEW MY BOOKINGS ↗</button>`);
      $("#viewBookings").onclick=()=>bookingsModal();
      toast("Booking confirmed!");
    }catch(err){$("#formMessage").textContent=err.message;toast(err.message,true);}
    finally{btn.disabled=false;}
  };
}
async function bookingsModal() {
  if(!currentUser){authModal("login");return;}
  try{
    const data=await api("/api/bookings");
    const list=data.bookings.length?data.bookings.map(b=>`<article class="booking-item"><h4>${esc(b.venue)} · #FC-${b.id}</h4><p>📍 ${esc(b.booking_date)} · ${esc(b.time_slot)}</p><p>₹${b.amount} · Payment: ${esc(b.payment_status)} · Status: ${esc(b.booking_status)}</p>${b.booking_status!=="Cancelled"?`<div class="inline-actions"><button class="mini-btn danger" data-cancel="${b.id}">CANCEL BOOKING</button></div>`:""}</article>`).join(""):`<div class="empty-state">No bookings yet. Your next game is waiting.</div>`;
    openModal(`${modalHead("YOUR ACCOUNT","MY BOOKINGS.","Your booking details are saved in the FanClub database.")}<div class="list-scroll">${list}</div><div class="inline-actions"><button class="mini-btn" id="newBooking">BOOK A GROUND</button><button class="mini-btn" id="profileBtn">MY PROFILE</button></div>`);
    $$("[data-cancel]").forEach(b=>b.onclick=async()=>{if(!confirm("Cancel this booking?"))return;try{const r=await api(`/api/bookings/${b.dataset.cancel}/cancel`,{method:"POST",body:"{}"});toast(r.message);bookingsModal();}catch(e){toast(e.message,true);}});
    $("#newBooking").onclick=()=>bookingModal();$("#profileBtn").onclick=profileModal;
  }catch(e){toast(e.message,true);}
}
async function profileModal(){
  try{const {profile:p}=await api("/api/profile");openModal(`${modalHead("PLAYER PROFILE","YOUR FANCLUB.","Update your contact details and keep your football profile current.")}<form id="profileForm" class="form-grid">${field("FULL NAME","profName","text","Name",true,p.name)}${field("PHONE NUMBER","profPhone","tel","Phone",true,p.phone)}<div class="summary-box"><div class="summary-row"><span>Email</span><strong>${esc(p.email)}</strong></div><div class="summary-row"><span>Bookings</span><strong>${p.bookings_count}</strong></div><div class="summary-row"><span>Teams joined</span><strong>${p.teams_count}</strong></div></div><p id="formMessage" class="form-message"></p><button class="btn full-btn">SAVE PROFILE ↗</button></form>`);
  $("#profileForm").onsubmit=async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{await api("/api/profile",{method:"PUT",body:JSON.stringify({name:f.get("profName"),phone:f.get("profPhone")})});currentUser.name=f.get("profName");currentUser.phone=f.get("profPhone");updateNav();toast("Profile updated.");profileModal();}catch(err){$("#formMessage").textContent=err.message;}};
  }catch(e){toast(e.message,true);}
}
function createTeamModal(){
  if(!currentUser){authModal("login");return;}
  openModal(`${modalHead("BUILD YOUR SQUAD","START A TEAM.","Create your local football team and invite players to join.")}<form id="teamForm" class="form-grid">${field("TEAM NAME","teamName","text","e.g. Kharghar Strikers")}${field("CITY / AREA","teamCity","text","e.g. Kharghar")}<div class="field"><label for="teamDesc">TEAM DESCRIPTION</label><textarea id="teamDesc" rows="3" placeholder="Tell players what your team is about"></textarea></div><p id="formMessage" class="form-message"></p><button class="btn full-btn">CREATE TEAM ↗</button></form>`);
  $("#teamForm").onsubmit=async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{const r=await api("/api/teams",{method:"POST",body:JSON.stringify({name:f.get("teamName"),city:f.get("teamCity"),description:$("#teamDesc").value})});toast(r.message);closeModal();refreshPublic();}catch(err){$("#formMessage").textContent=err.message;toast(err.message,true);}};
}
async function teamDetails(id){
  try{
    const [teams,members]=await Promise.all([api("/api/teams"),api(`/api/teams/${id}/members`)]);
    const team=teams.teams.find(t=>t.id===id);if(!team){toast("Team not found.",true);return;}
    const mine=members.members.some(m=>currentUser&&m.id===currentUser.id);
    openModal(`${modalHead("MEET THE SQUAD",esc(team.name),`${esc(team.city)} · Captain: ${esc(team.captain)} · ${team.member_count} members`)}<p>${esc(team.description||"A local team ready to play.")}</p><h3>TEAM MEMBERS</h3><div class="list-scroll">${members.members.map(m=>`<article class="booking-item"><h4>${esc(m.name)} ${m.role==="Captain"?"· CAPTAIN":""}</h4><p>Joined ${esc(m.joined_at)}</p></article>`).join("")||"No members yet."}</div><div class="inline-actions">${currentUser?`<button class="btn" id="teamJoin">${mine?"LEAVE TEAM":"JOIN TEAM"} ↗</button>`:`<button class="btn" id="teamLogin">LOGIN TO JOIN ↗</button>`}</div>`);
    if(!currentUser)$("#teamLogin").onclick=()=>authModal("login");
    else $("#teamJoin").onclick=async()=>{try{const r=await api(`/api/teams/${id}/${mine?"leave":"join"}`,{method:"POST",body:"{}"});toast(r.message);teamDetails(id);refreshPublic();}catch(e){toast(e.message,true);}};
  }catch(e){toast(e.message,true);}
}
async function refreshPublic(){
  try{
    const [teamsData,matchesData]=await Promise.all([api("/api/teams"),api("/api/matches")]);
    $("#teamCount").textContent=teamsData.teams.length;
    const featured=teamsData.teams.find(t=>t.name==="Kharghar Strikers");
    if(featured){try{const m=await api(`/api/teams/${featured.id}/members`);$("#memberCount").textContent=m.members.length;}catch{}}
    $("#teamList").innerHTML=teamsData.teams.map(t=>`<div class="team-mini"><span><strong>${esc(t.name)}</strong><br><span class="muted-small">${esc(t.city)} · ${t.member_count} players</span></span><button data-team="${t.id}">VIEW ↗</button></div>`).join("")||`<div class="team-mini">No teams yet. Create the first team.</div>`;
    $$("[data-team]").forEach(b=>b.onclick=()=>teamDetails(Number(b.dataset.team)));
    $("#matchList").innerHTML=matchesData.matches.map(m=>`<article class="match-card"><div class="match-date">${esc(m.match_date)} · ${esc(m.match_time)}</div><div class="match-versus"><div class="match-team">${esc(m.home_team)}</div><div class="versus">VS</div><div class="match-team" style="text-align:right">${esc(m.away_team)}</div></div><div class="match-meta"><span>⌖ ${esc(m.venue)}</span><span class="match-status">${esc(m.status)}</span></div></article>`).join("")||`<div class="empty-state">No fixtures yet. Check back soon.</div>`;
  }catch(e){console.error(e);}
}
function updateNav(){
  const auth=$("#authNav"),logout=$("#logoutBtn");
  if(currentUser){auth.textContent=currentUser.name.split(" ")[0].toUpperCase();auth.dataset.open="profile";logout.classList.remove("hidden");}
  else{auth.textContent="LOGIN / JOIN";auth.dataset.open="login";logout.classList.add("hidden");}
}
async function adminModal(){
  if(!currentUser){authModal("login");return;}
  if(currentUser.role!=="admin"){toast("Admin access only.",true);return;}
  adminTab="overview";await renderAdmin();
}
async function renderAdmin(){
  try{
    const [statsData,usersData,bookingsData,teamsData,matchesData]=await Promise.all([
      api("/api/admin/stats"),api("/api/admin/users"),api("/api/admin/bookings"),api("/api/admin/teams"),api("/api/admin/matches")
    ]);
    let body="";
    if(adminTab==="overview"){const s=statsData.stats;body=`<div class="stat-grid">${[["USERS",s.users],["BOOKINGS",s.bookings],["TEAMS",s.teams],["MATCHES",s.matches],["DEMO REVENUE",`₹${s.revenue}`]].map(([a,b])=>`<div class="stat-card"><strong>${b}</strong><small>${a}</small></div>`).join("")}</div><p class="muted-small">Revenue counts only simulated successful payments. This is demo data stored in SQLite.</p>`;}
    if(adminTab==="users")body=`<div class="list-scroll">${usersData.users.map(u=>`<article class="admin-item"><h4>${esc(u.name)} ${u.role==="admin"?"· ADMIN":""}</h4><p>${esc(u.email)} · ${esc(u.phone)}</p><p class="muted-small">Joined ${esc(u.created_at)}</p>${u.role!=="admin"?`<button class="mini-btn danger" data-deluser="${u.id}">DELETE USER</button>`:""}</article>`).join("")}</div>`;
    if(adminTab==="bookings")body=`<div class="list-scroll">${bookingsData.bookings.map(b=>`<article class="admin-item"><h4>#FC-${b.id} · ${esc(b.name)}</h4><p>${esc(b.venue)} · ${esc(b.booking_date)} · ${esc(b.time_slot)}</p><p>₹${b.amount} · ${esc(b.payment_status)} · ${esc(b.booking_status)}</p>${b.booking_status!=="Cancelled"?`<button class="mini-btn danger" data-admincancel="${b.id}">CANCEL</button>`:""}</article>`).join("")||"No bookings yet."}</div>`;
    if(adminTab==="teams")body=`<div class="list-scroll">${teamsData.teams.map(t=>`<article class="admin-item"><h4>${esc(t.name)}</h4><p>${esc(t.city)} · Captain: ${esc(t.captain)}</p><button class="mini-btn danger" data-delteam="${t.id}">DELETE TEAM</button></article>`).join("")}</div>`;
    if(adminTab==="matches")body=`<form id="matchForm" class="form-grid">${field("HOME TEAM","homeTeam","text","Home team")}${field("AWAY TEAM","awayTeam","text","Away team")}<div class="form-two">${field("DATE","matchDate","date","",true,"")}${field("TIME","matchTime","text","e.g. 8:00 PM")}</div>${field("VENUE","matchVenue","text","Venue",true,"Ryan Vibgyor KPC Empyrean")}<button class="btn full-btn">SCHEDULE MATCH ↗</button></form><div class="list-scroll">${matchesData.matches.map(m=>`<article class="admin-item"><h4>${esc(m.home_team)} vs ${esc(m.away_team)}</h4><p>${esc(m.match_date)} · ${esc(m.match_time)} · ${esc(m.status)}</p><button class="mini-btn danger" data-delmatch="${m.id}">DELETE MATCH</button></article>`).join("")}</div>`;
    openModal(`${modalHead("FANCLUB CONTROL ROOM","ADMIN DASHBOARD.","Manage the community. All changes are saved in the database.")}<div class="admin-tabs">${[["overview","OVERVIEW"],["users","USERS"],["bookings","BOOKINGS"],["teams","TEAMS"],["matches","MATCHES"]].map(([key,label])=>`<button data-admintab="${key}" class="${adminTab===key?"active":""}">${label}</button>`).join("")}</div><div id="adminBody">${body}</div>`);
    $$("[data-admintab]").forEach(b=>b.onclick=()=>{adminTab=b.dataset.admintab;renderAdmin();});
    $$("[data-deluser]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this user?")){try{await api(`/api/admin/users/${b.dataset.deluser}`,{method:"DELETE"});toast("User deleted.");renderAdmin();}catch(e){toast(e.message,true);}}});
    $$("[data-admincancel]").forEach(b=>b.onclick=async()=>{try{await api(`/api/admin/bookings/${b.dataset.admincancel}/cancel`,{method:"POST",body:"{}"});toast("Booking cancelled.");renderAdmin();}catch(e){toast(e.message,true);}});
    $$("[data-delteam]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this team?")){try{await api(`/api/admin/teams/${b.dataset.delteam}`,{method:"DELETE"});toast("Team deleted.");refreshPublic();renderAdmin();}catch(e){toast(e.message,true);}}});
    $$("[data-delmatch]").forEach(b=>b.onclick=async()=>{if(confirm("Delete this match?")){try{await api(`/api/matches/${b.dataset.delmatch}`,{method:"DELETE"});toast("Match deleted.");refreshPublic();renderAdmin();}catch(e){toast(e.message,true);}}});
    if($("#matchForm")){$("#matchDate").min=new Date().toISOString().slice(0,10);$("#matchForm").onsubmit=async e=>{e.preventDefault();const f=new FormData(e.currentTarget);try{const r=await api("/api/matches",{method:"POST",body:JSON.stringify({home_team:f.get("homeTeam"),away_team:f.get("awayTeam"),match_date:f.get("matchDate"),match_time:f.get("matchTime"),venue:f.get("matchVenue")})});toast(r.message);refreshPublic();renderAdmin();}catch(err){toast(err.message,true);}};}
  }catch(e){toast(e.message,true);if(e.message.includes("Admin"))closeModal();}
}
document.addEventListener("click",e=>{
  const opener=e.target.closest("[data-open]");
  if(opener){const action=opener.dataset.open;if(action==="login"||action==="register")authModal(action);else if(action==="bookings")bookingsModal();else if(action==="createTeam")createTeamModal();else if(action==="admin")adminModal();else if(action==="profile")profileModal();}
});
$("#modalClose").onclick=closeModal;
$("#modalBackdrop").addEventListener("click",e=>{if(e.target===$("#modalBackdrop"))closeModal();});
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();});
$$(".slot").forEach(b=>b.addEventListener("click",()=>{$$(".slot").forEach(x=>x.classList.remove("selected"));b.classList.add("selected");selectedSlot=b.dataset.slot;bookingModal(selectedSlot);}));
$("#bookVenueBtn").onclick=()=>bookingModal(selectedSlot);
$("#mobileToggle").onclick=()=>$("#mainNav").classList.toggle("open");
$$('#mainNav a').forEach(a=>a.addEventListener("click",()=>$("#mainNav").classList.remove("open")));
$("#logoutBtn").onclick=async()=>{try{await api("/api/logout",{method:"POST",body:"{}"});currentUser=null;updateNav();toast("Logged out.");closeModal();}catch(e){toast(e.message,true);}};
(async function init(){
  try{const data=await api("/api/me");currentUser=data.user;updateNav();}catch{}
  await refreshPublic();
  if(window.FANCLUB_CONFIG?.openAuth)authModal(window.FANCLUB_CONFIG.openAuth);
  if(window.FANCLUB_CONFIG?.openAdmin)adminModal();
})();
