import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  CircleGauge,
  Compass,
  Cuboid,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  MessageSquare,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UserRound,
  X,
  Zap
} from "lucide-react";
import API from "./services/api";

const fallbackAlumni = [
  { alumni_id: 2, name: "Vikram Reddy", current_role: "Senior ML Engineer", company: "Microsoft", match_score: 94, reason: "Python, MLOps and machine learning overlap with your Career DNA." },
  { alumni_id: 3, name: "Ananya Rao", current_role: "Product Data Scientist", company: "Atlassian", match_score: 87, reason: "Strong fit for your analytics and product experimentation goals." },
  { alumni_id: 4, name: "Karthik Menon", current_role: "Cloud Solutions Architect", company: "AWS", match_score: 79, reason: "Can help you translate projects into production-grade cloud systems." }
];

const opportunities = [
  { title: "AI Engineering Intern", company: "Microsoft", type: "Internship", location: "Hyderabad · Hybrid", skills: ["Python", "ML"], deadline: "30 Oct 2026", accent: "violet" },
  { title: "Data Science Challenge", company: "HITAM Innovation Cell", type: "Challenge", location: "Campus · 48 hours", skills: ["SQL", "Pandas"], deadline: "12 Oct 2026", accent: "orange" },
  { title: "Women in Tech Fellowship", company: "Atlassian", type: "Fellowship", location: "Remote · India", skills: ["Analytics", "Product"], deadline: "04 Nov 2026", accent: "cyan" }
];

const navItems = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "opportunities", label: "Opportunity radar", icon: Compass },
  { id: "galaxy", label: "Opportunity galaxy", icon: Target },
  { id: "network", label: "Alumni network", icon: Network },
  { id: "constellation", label: "Career constellation", icon: Cuboid },
  { id: "messages", label: "Messages", icon: MessageSquare },
  { id: "profile", label: "My profile", icon: UserRound },
  { id: "toolkit", label: "AI toolkit", icon: Sparkles }
];

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [role, setRole] = useState(localStorage.getItem("role") || "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mustChangePassword, setMustChangePassword] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState("overview");
  const [mobileNav, setMobileNav] = useState(false);
  const [userData, setUserData] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [careerDna, setCareerDna] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [savedAlumni, setSavedAlumni] = useState(() => JSON.parse(localStorage.getItem("savedAlumni") || "[]"));
  const [toast, setToast] = useState("");
  const [connections, setConnections] = useState([]);
  const [dataMode, setDataMode] = useState({ label: "Synthetic Dataset", mode: "synthetic" });
  const effectiveRole = userData?.role || role || "STUDENT";
  const visibleNavItems = [
    ...(effectiveRole === "ALUMNI"
      ? navItems.map((item) => item.id === "network" ? { ...item, label: "Student network" } : item)
      : navItems),
    ...(effectiveRole === "ADMIN" ? [{ id: "admin", label: "Admin center", icon: ShieldCheck }] : []),
    { id: "requests", label: effectiveRole === "ALUMNI" ? "Requests" : "My requests", icon: Send }
  ];

  useEffect(() => {
    if (token) fetchDashboardData();
  }, [token]);

  useEffect(() => {
    if (!token) return;
    API.get("/platform/data-mode").then((response) => setDataMode(response.data)).catch(() => {});
  }, [token]);

  useEffect(() => {
    localStorage.setItem("savedAlumni", JSON.stringify(savedAlumni));
  }, [savedAlumni]);

  const notify = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2600);
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");
    try {
      const response = await API.post("/auth/login", {
        email: email,
        password: password
      });
      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("role", response.data.role);
      setToken(response.data.access_token);
      setRole(response.data.role);
      setMustChangePassword(response.data.must_change_password);
    } catch (err) {
      setError(err.response?.data?.detail || "We couldn’t verify those details. Check the email and password.");
    }
  };

  const changeInitialPassword = async (event) => {
    event.preventDefault();
    if (newPassword.length < 8) return setError("Your new password must contain at least 8 characters.");
    if (newPassword !== passwordConfirmation) return setError("The new passwords do not match.");
    try {
      await API.post("/auth/change-password", { current_password: password, new_password: newPassword });
      setMustChangePassword(false);
      setPassword("");
      setNewPassword("");
      setPasswordConfirmation("");
      setError("");
      notify("Password updated. Welcome to your command center.");
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to update your password.");
    }
  };

  const fetchDashboardData = async () => {
    try {
      const userResponse = await API.get("/users/me");
      setUserData(userResponse.data);
      const connectionResponse = await API.get("/connections");
      setConnections(connectionResponse.data);
      if (userResponse.data.role === "STUDENT") {
        const [matches, dna] = await Promise.allSettled([API.get("/recommendations/alumni"), API.get("/career-dna")]);
        if (matches.status === "fulfilled" && matches.value.data.length) {
          setRecommendations(matches.value.data);
        } else {
          const alumniResponse = await API.get("/alumni");
          setRecommendations(alumniResponse.data.map((alum) => ({
            alumni_id: alum.id,
            name: alum.name,
            current_role: alum.current_role,
            company: alum.company,
            match_score: 0,
            reason: "Explore this alumni profile and start a conversation."
          })));
        }
        setCareerDna(dna.status === "fulfilled" ? dna.value.data : { primary_goal: "Machine Learning Engineer", missing_skills: ["Docker", "System design"] });
      }
      if (userResponse.data.role === "ADMIN") {
        const response = await API.get("/admin/analytics");
        setAnalytics(response.data);
      }
    } catch {
      setRecommendations(fallbackAlumni);
      setCareerDna({ primary_goal: "Machine Learning Engineer", missing_skills: ["Docker", "System design"] });
    }
  };

  const requestMentorship = async (alumniId, name) => {
    try {
      await API.post("/mentorship/request", { alumni_user_id: alumniId, skill: "Machine Learning", message: "Hello! Looking for mentorship." });
      notify(`Request sent to ${name}`);
    } catch {
      notify("Your request is queued for the next sync.");
    }
  };

  const requestConnection = async (alumniId, name) => {
    try {
      await API.post("/connections/request", { alumni_user_id: alumniId });
      notify(`Connection request sent to ${name}`);
      const response = await API.get("/connections");
      setConnections(response.data);
    } catch (err) {
      notify(err.response?.data?.detail || "Unable to send connection request.");
    }
  };

  const toggleSaved = (id) => {
    setSavedAlumni((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
    notify(savedAlumni.includes(id) ? "Mentor removed from your orbit" : "Mentor saved to your orbit");
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    setToken("");
    setUserData(null);
  };

  if (!token) {
    return (
      <div className="login-shell">
        <div className="login-art">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <span className="eyebrow"><Sparkles size={14} /> HITAM · ALUMNIFORGE</span>
          <h1>Build a career<br /><em>worth mapping.</em></h1>
          <p>One intelligent layer between your campus story and the people, skills and opportunities that move it forward.</p>
          <div className="login-note"><Zap size={16} /><span><strong>Career intelligence, not another job board.</strong><br />Your next move is already closer than you think.</span></div>
        </div>
        <div className="login-panel">
          <div className="brand-mark"><ShieldCheck size={19} /> <span>AlumniForge</span></div>
          <div className="login-copy"><span className="eyebrow muted">WELCOME BACK</span><h2>Enter your command center</h2><p>Sign in to reconnect with your future.</p></div>
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={handleLogin} className="login-form">
            <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@hitam.org" required /></label>
            <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" required /></label>
            <button className="primary-button" type="submit">Enter dashboard <ArrowUpRight size={17} /></button>
          </form>
          <div className="demo-accounts"><span>DEMO ACCESS</span><p><b>Student</b> rahul@hitam.org · 230101</p><p><b>Alumni</b> vikram.alumni@hitam.org · ALUM2020</p><p><b>Admin</b> admin@hitam.org · Admin@123</p><small>Dataset accounts: use any email from the CSV files with password <b>12345</b>. First login asks you to create a private password.</small></div>
        </div>
      </div>
    );
  }

  if (mustChangePassword) {
    return (
      <div className="login-shell">
        <div className="login-art">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <span className="eyebrow"><ShieldCheck size={14} /> ACCOUNT SECURITY</span>
          <h1>Make your<br /><em>first move.</em></h1>
          <p>Your account was created with a temporary password. Choose a private password before entering AlumniForge.</p>
        </div>
        <div className="login-panel">
          <div className="brand-mark"><ShieldCheck size={19} /> <span>AlumniForge</span></div>
          <div className="login-copy"><span className="eyebrow muted">ONE-TIME SETUP</span><h2>Create your private key</h2><p>This protects your account and cannot be skipped.</p></div>
          {error && <div className="error-message">{error}</div>}
          <form onSubmit={changeInitialPassword} className="login-form">
            <label>New password<input type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} placeholder="At least 8 characters" required minLength={8} /></label>
            <label>Confirm new password<input type="password" value={passwordConfirmation} onChange={(event) => setPasswordConfirmation(event.target.value)} placeholder="Repeat your new password" required /></label>
            <button className="primary-button" type="submit">Secure my account <ArrowUpRight size={17} /></button>
          </form>
        </div>
      </div>
    );
  }

  const displayName = userData?.name || "Rahul";
  return (
    <div className="app-shell">
      {toast && <div className="toast"><Check size={15} /> {toast}</div>}
      <aside className={`sidebar ${mobileNav ? "open" : ""}`}>
        <div className="brand-mark"><ShieldCheck size={19} /> <span>AlumniForge</span></div>
        <div className="workspace-label">YOUR WORKSPACE</div>
        <nav>{visibleNavItems.map(({ id, label, icon: Icon }) => <button key={id} className={activeView === id ? "active" : ""} onClick={() => { setActiveView(id); setMobileNav(false); }}><Icon size={17} />{label}{id === "opportunities" && <span className="nav-dot" />}</button>)}</nav>
        <div className="sidebar-bottom"><div className="mini-profile"><div className="avatar">{displayName.charAt(0)}</div><div><strong>{displayName}</strong><small>{role.toLowerCase()}</small></div></div><button className="logout-button" onClick={logout}><LogOut size={16} /></button></div>
      </aside>
      <main className="content">
        <header className="topbar"><button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)}><Menu size={20} /></button><div className="breadcrumb"><span>Workspace</span><ChevronRight size={14} /><strong>{visibleNavItems.find((item) => item.id === activeView)?.label}</strong></div><div className="top-actions"><span className={`data-badge ${dataMode.mode === "live" ? "live" : ""}`}><i /> {dataMode.label}</span><div className="search-pill"><Search size={16} /><input placeholder="Search your network..." /></div><div className="notification-dot" /><div className="top-avatar">{displayName.charAt(0)}</div></div></header>
        <div className="page-body">
          {activeView === "overview" && (effectiveRole === "ALUMNI"
            ? <AlumniOverview profile={userData?.profile} connections={connections} setActiveView={setActiveView} />
            : <Overview name={displayName} careerDna={careerDna} recommendations={recommendations} savedAlumni={savedAlumni} toggleSaved={toggleSaved} requestMentorship={requestMentorship} requestConnection={requestConnection} setActiveView={setActiveView} />)}
          {activeView === "opportunities" && <OpportunityRadar notify={notify} profile={userData?.profile} />}
          {activeView === "galaxy" && <OpportunityGalaxy profile={userData?.profile} notify={notify} />}
          {activeView === "network" && <NetworkView recommendations={recommendations} savedAlumni={savedAlumni} toggleSaved={toggleSaved} requestMentorship={requestMentorship} requestConnection={requestConnection} />}
          {activeView === "constellation" && <CareerConstellation profile={userData?.profile} careerDna={careerDna} role={effectiveRole} setActiveView={setActiveView} />}
          {activeView === "messages" && <MessagesView connections={connections} currentUserId={userData?.id} notify={notify} />}
          {activeView === "admin" && role === "ADMIN" && analytics && <AdminOverview analytics={analytics} />}
          {activeView === "requests" && (effectiveRole === "ALUMNI"
            ? <AlumniRequests notify={notify} refreshConnections={() => API.get("/connections").then((response) => setConnections(response.data))} />
            : <StudentRequests connections={connections} notify={notify} />)}
          {activeView === "profile" && <ProfileView profile={userData?.profile} role={effectiveRole} name={displayName} notify={notify} onSaved={fetchDashboardData} />}
          {activeView === "toolkit" && <Toolkit notify={notify} profile={userData?.profile} role={effectiveRole} />}
          {role === "ADMIN" && analytics && activeView !== "admin" && <div className="admin-strip"><CircleGauge size={18} /><span>Admin pulse</span><b>{analytics.summary?.total_users || analytics.total_users || analytics.summary?.total_students || 0}</b> total platform members · <b>{analytics.summary?.active_connections || analytics.connections || 0}</b> active connections</div>}
        </div>
      </main>
    </div>
  );
}

function ProfileView({ profile = {}, role, name, notify, onSaved }) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  useEffect(() => setForm({
    name: profile.name || name,
    location: profile.location || "",
    bio: profile.bio || "",
    skills: (profile.skills || []).join(", "),
    interests: (profile.interests || []).join(", "),
    projects: (profile.projects || []).join("\n")
  }), [profile, name]);
  const save = async (event) => {
    event.preventDefault();
    try {
      await API.put("/users/me", {
        name: form.name,
        location: form.location,
        bio: form.bio,
        skills: form.skills.split(",").map((item) => item.trim()).filter(Boolean),
        interests: form.interests.split(",").map((item) => item.trim()).filter(Boolean),
        projects: form.projects.split("\n").map((item) => item.trim()).filter(Boolean)
      });
      notify("Profile signal updated.");
      setEditing(false);
      onSaved();
    } catch (error) {
      notify(error.response?.data?.detail || "Unable to update your profile.");
    }
  };
  const chips = (items) => <div className="profile-chips">{(items || []).length ? items.map((item) => <span key={item}>{item}</span>) : <small>No details added yet.</small>}</div>;
  return <div className="view-stack">
    <div className="profile-banner"><div className="avatar xl">{(profile.name || name || "A").charAt(0)}</div><div><span className="eyebrow">{role === "ALUMNI" ? "ALUMNI SIGNAL" : "STUDENT SIGNAL"}</span><h1>{profile.name || name}</h1><p>{role === "ALUMNI" ? `${profile.current_role || "Industry professional"} · ${profile.company || "Career builder"}` : `${profile.target_role || profile.career_goal || "Emerging professional"} · ${profile.branch || "HITAM"}`}</p></div><button className="primary-button compact" onClick={() => setEditing((value) => !value)}>{editing ? "Close editor" : "Tune profile"}</button></div>
    {editing && <form className="profile-editor" onSubmit={save}><label>Name<input value={form.name || ""} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label><label>Location<input value={form.location || ""} onChange={(event) => setForm({ ...form, location: event.target.value })} /></label><label>Skills <small>comma separated</small><input value={form.skills || ""} onChange={(event) => setForm({ ...form, skills: event.target.value })} /></label><label>Interests <small>comma separated</small><input value={form.interests || ""} onChange={(event) => setForm({ ...form, interests: event.target.value })} /></label><label className="wide-field">Bio<textarea value={form.bio || ""} onChange={(event) => setForm({ ...form, bio: event.target.value })} /></label><label className="wide-field">Projects <small>one project per line</small><textarea value={form.projects || ""} onChange={(event) => setForm({ ...form, projects: event.target.value })} /></label><button className="primary-button" type="submit">Save profile <Check size={15} /></button></form>}
    <div className="profile-grid"><section className="profile-panel"><span className="eyebrow muted">IDENTITY</span><h2>Profile constellation</h2><div className="detail-list"><div><small>LOCATION</small><strong>{profile.location || "Not added"}</strong></div><div><small>BRANCH / DEGREE</small><strong>{[profile.branch, profile.degree].filter(Boolean).join(" · ") || "Not added"}</strong></div><div><small>GRADUATION</small><strong>{profile.graduation_year || "Not added"}</strong></div>{role === "ALUMNI" && <><div><small>EXPERIENCE</small><strong>{profile.years_experience || 0} years</strong></div><div><small>INDUSTRY</small><strong>{profile.industry || "Not added"}</strong></div></>}</div></section><section className="profile-panel"><span className="eyebrow muted">SKILLS & INTERESTS</span><h2>Your working vocabulary</h2><small className="profile-label">SKILLS</small>{chips(profile.skills)}<small className="profile-label">INTERESTS</small>{chips(profile.interests || profile.mentorship_expertise)}</section></div>
    <div className="profile-grid"><section className="profile-panel"><span className="eyebrow muted">PROJECTS</span><h2>Proof of work</h2><div className="project-list">{(profile.projects || []).length ? profile.projects.map((project, index) => <div className="project-item" key={`${project}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span><p>{project}</p></div>) : <small>No projects added yet.</small>}</div></section><section className="profile-panel"><span className="eyebrow muted">STORY</span><h2>{role === "ALUMNI" ? "Career journey" : "About your trajectory"}</h2><p className="profile-copy">{profile.bio || "Add a short story so the right people can discover your journey."}</p>{role === "ALUMNI" && profile.career_journey && <div className="journey-line">{profile.career_journey}</div>}</section></div>
  </div>;
}

function AlumniOverview({ profile = {}, connections, setActiveView }) {
  const pending = connections.filter((item) => item.status === "Pending").length;
  return <div className="view-stack"><section className="hero-card"><div><span className="eyebrow">ALUMNI STUDIO · KNOWLEDGE TRANSFER</span><h1>Build your legacy, {profile.name?.split(" ")[0] || "mentor"} <span>✦</span></h1><p>Your experience can become someone else's shortest path to their next breakthrough.</p><button className="ghost-light" onClick={() => setActiveView("requests")}>Review your requests <ArrowUpRight size={16} /></button></div><div className="hero-orbit"><div className="orbit-ring ring-a" /><div className="orbit-ring ring-b" /><BriefcaseBusiness size={36} /></div></section><div className="stat-grid"><div className="stat-card"><span>EXPERIENCE</span><strong>{profile.years_experience || 0}<span> yrs</span></strong><small>{profile.current_role || "Industry professional"}</small></div><div className="stat-card"><span>MENTORSHIP SIGNAL</span><strong>{(profile.mentorship_expertise || profile.skills || []).length}</strong><small>skills you can unlock for students</small></div><div className="stat-card"><span>OPEN REQUESTS</span><strong>{String(pending).padStart(2, "0")}</strong><small>people waiting in your orbit</small></div></div><div className="profile-grid"><section className="profile-panel"><span className="eyebrow muted">YOUR EDGE</span><h2>{profile.company || "Your career story"}</h2><p className="profile-copy">{profile.bio || "Complete your profile to help students understand your path."}</p>{profile.location && <div className="journey-line">Based in {profile.location}</div>}</section><section className="profile-panel"><span className="eyebrow muted">MENTOR TOOLKIT</span><h2>What you can unlock</h2>{(profile.skills || []).slice(0, 6).map((skill) => <span className="signal-pill" key={skill}>{skill}</span>)}<button className="text-button" onClick={() => setActiveView("profile")}>View full profile <ChevronRight size={15} /></button></section></div></div>;
}

function CareerConstellation({ profile = {}, careerDna = {}, role, setActiveView }) {
  const profileSkills = Array.isArray(profile.skills) ? profile.skills : [];
  const profileInterests = Array.isArray(profile.interests) ? profile.interests : [];
  const dnaSkills = Array.isArray(careerDna.strong_skills) ? careerDna.strong_skills : [];
  const skills = [...new Set([...profileSkills, ...profileInterests, ...dnaSkills].filter(Boolean))].slice(0, 8);
  const visibleSkills = skills.length ? skills : ["Python", "Communication", "Problem solving"];
  const missing = Array.isArray(careerDna.missing_skills) && careerDna.missing_skills.length
    ? careerDna.missing_skills
    : ["Docker", "System design", "Cloud deployment"];
  const journey = profile.career_journey || [];
  const [selected, setSelected] = useState(visibleSkills[0]);
  useEffect(() => setSelected(visibleSkills[0]), [profile.id, careerDna.primary_goal]);
  return <div className="view-stack">
    <div className="page-intro"><div><span className="eyebrow">3D CAREER GRAPH · LIVE PROFILE SIGNAL</span><h1>Career constellation</h1><p>See the skills, people and next moves orbiting your story.</p></div><div className="constellation-status"><i /> Profile synced</div></div>
    <section className="constellation-hero">
      <div className="constellation-copy"><span className="eyebrow">YOUR PROFESSIONAL GRAVITY</span><h2>{profile.target_role || profile.current_role || "Your next role"}</h2><p>{role === "ALUMNI" ? "Your experience is a navigable map for the next generation." : "Your strongest signals are forming a path toward the role you want."}</p><div className="constellation-legend"><span><i className="legend-core" /> Core signal</span><span><i className="legend-skill" /> Proven skill</span><span><i className="legend-gap" /> Unlock next</span></div></div>
      <div className="orbit-stage" aria-label="Interactive 3D career constellation"><div className="orbit-plane plane-one" /><div className="orbit-plane plane-two" /><div className="orbit-core"><Sparkles size={20} /><small>{selected}</small></div>{visibleSkills.map((skill, index) => <button className={`orbit-node node-${index + 1}`} key={skill} onClick={() => setSelected(skill)}>{skill}</button>)}<span className="orbit-satellite satellite-a" /><span className="orbit-satellite satellite-b" /></div>
    </section>
    <div className="constellation-grid"><section className="profile-panel"><span className="eyebrow muted">SIGNAL INSPECTOR</span><h2>{selected}</h2><p className="profile-copy">{(profile.skills || []).includes(selected) ? "This signal is already present in your profile and contributes to your match strength." : "This is an adjacent signal that can expand your discovery surface."}</p><div className="signal-meter"><span style={{ width: (profile.skills || []).includes(selected) ? "86%" : "32%" }} /></div><small>{(profile.skills || []).includes(selected) ? "Established signal" : "Opportunity signal"}</small></section><section className="profile-panel"><span className="eyebrow muted">NEXT UNLOCKS</span><h2>Close one orbit</h2>{missing.slice(0, 3).map((item, index) => <button className="unlock-row" key={item} onClick={() => setActiveView("toolkit")}><span>0{index + 1}</span><strong>{item}</strong><ChevronRight size={15} /></button>)}</section></div>
    <section className="profile-panel trajectory-panel"><span className="eyebrow muted">TRAJECTORY LOG</span><h2>How your story moves</h2><div className="trajectory-line">{(journey.length ? journey : [profile.bio || "Add your first career milestone from My profile."]).map((item, index) => <div className="trajectory-stop" key={`${item}-${index}`}><i /><p>{item}</p></div>)}</div></section>
  </div>;
}

function OpportunityGalaxy({ profile = {}, notify }) {
  const [selected, setSelected] = useState(0);
  const profileSkills = (profile.skills || []).map((item) => item.toLowerCase());
  const missions = opportunities.map((item) => {
    const overlap = item.skills.filter((skill) => profileSkills.some((mine) => mine.includes(skill.toLowerCase()) || skill.toLowerCase().includes(mine)));
    return { ...item, fit: Math.min(98, 54 + overlap.length * 16), overlap };
  });
  const active = missions[selected] || missions[0];
  return <div className="view-stack">
    <div className="page-intro"><div><span className="eyebrow">3D OPPORTUNITY MAP · PROFILE-AWARE</span><h1>Opportunity galaxy</h1><p>Every opening is a planet. Your skills decide which worlds are closest.</p></div><button className="primary-button compact" onClick={() => notify("Galaxy recalibrated around your latest profile signals.")}><Zap size={15} /> Recalibrate</button></div>
    <section className="galaxy-stage"><div className="galaxy-copy"><span className="eyebrow">MISSION CONTROL</span><h2>Choose your next orbit.</h2><p>Explore the opportunity field, then convert one signal into a concrete next move.</p><div className="galaxy-readout"><small>ACTIVE MISSION</small><strong>{active.title}</strong><span>{active.fit}% profile resonance</span></div></div><div className="galaxy-viewport"><div className="galaxy-grid" /><div className="galaxy-sun"><Zap size={18} /></div>{missions.map((mission, index) => <button key={mission.title} className={`galaxy-planet planet-${index + 1} ${selected === index ? "selected" : ""}`} onClick={() => setSelected(index)}><i /> <span>{mission.title}</span></button>)}<span className="galaxy-star star-one" /><span className="galaxy-star star-two" /><span className="galaxy-star star-three" /></div></section>
    <div className="galaxy-detail-grid"><section className="profile-panel"><span className="eyebrow muted">MISSION BRIEF</span><h2>{active.title}</h2><p className="profile-copy">{active.company} · {active.location}</p><div className="mission-tags">{active.skills.map((skill) => <span key={skill} className={active.overlap.includes(skill) ? "matched" : ""}>{skill}{active.overlap.includes(skill) && " · matched"}</span>)}</div><button className="primary-button compact" onClick={() => notify(`Launch plan created for ${active.title}`)}>Create launch plan <ArrowUpRight size={15} /></button></section><section className="profile-panel"><span className="eyebrow muted">ORBIT SIGNALS</span><h2>Why this is close</h2><div className="orbit-metrics"><div><strong>{active.fit}%</strong><small>resonance</small></div><div><strong>{active.overlap.length}</strong><small>skill overlaps</small></div><div><strong>{active.deadline.split(" ")[0]}</strong><small>deadline day</small></div></div><div className="journey-line">Best next move: add one proof point that connects your profile to {active.skills[0]}.</div></section></div>
  </div>;
}

function Overview({ name, careerDna, recommendations, savedAlumni, toggleSaved, requestMentorship, requestConnection, setActiveView }) {
  const skills = careerDna?.missing_skills || ["Docker", "System design", "MLOps"];
  return <div className="view-stack">
    <section className="hero-card"><div><span className="eyebrow">MONDAY · 21 SEPTEMBER 2026</span><h1>Good morning, {name.split(" ")[0]} <span>✦</span></h1><p>Your next meaningful connection is <strong>2 degrees away.</strong></p><button className="ghost-light" onClick={() => setActiveView("toolkit")}>Open your AI toolkit <ArrowUpRight size={16} /></button></div><div className="hero-orbit"><div className="orbit-ring ring-a" /><div className="orbit-ring ring-b" /><Target size={36} /></div></section>
    <div className="stat-grid"><div className="stat-card"><span>CAREER READINESS</span><strong>76<span>%</span></strong><div className="progress"><i style={{ width: "76%" }} /></div><small><TrendingUp size={13} /> +8% this month</small></div><div className="stat-card"><span>NETWORK REACH</span><strong>24</strong><small>people in your orbit</small><div className="mini-bars"><i /><i /><i /><i /><i /></div></div><div className="stat-card"><span>OPEN LOOPS</span><strong>03</strong><small>conversations to follow up</small><div className="open-loop"><span /><span /><span /></div></div></div>
    <div className="section-heading"><div><span className="eyebrow muted">YOUR SIGNAL</span><h2>Career DNA</h2></div><button className="text-button" onClick={() => setActiveView("toolkit")}>Tune profile <ChevronRight size={16} /></button></div>
    <section className="dna-card"><div className="dna-main"><div className="dna-icon"><Sparkles size={20} /></div><div><span className="eyebrow">PRIMARY TRAJECTORY</span><h3>{careerDna?.primary_goal || "Machine Learning Engineer"}</h3><p>Your profile is resonating with builders who combine data fluency with shipping instincts.</p></div></div><div className="skill-list">{skills.slice(0, 3).map((skill) => <span key={skill}>{skill}<small>gap</small></span>)}</div></section>
    <div className="section-heading"><div><span className="eyebrow muted">HIGH-SIGNAL PEOPLE</span><h2>Mentors in your orbit</h2></div><button className="text-button" onClick={() => setActiveView("network")}>View all <ChevronRight size={16} /></button></div>
    <div className="mentor-grid">{recommendations.slice(0, 3).map((alum) => <MentorCard key={alum.alumni_id} alum={alum} saved={savedAlumni.includes(alum.alumni_id)} toggleSaved={toggleSaved} requestMentorship={requestMentorship} requestConnection={requestConnection} />)}</div>
  </div>;
}

function MentorCard({ alum, saved, toggleSaved, requestMentorship, requestConnection }) {
  return <article className="mentor-card"><div className="card-top"><div className="avatar large">{alum.name?.charAt(0) || "A"}</div><button className={`save-button ${saved ? "saved" : ""}`} onClick={() => toggleSaved(alum.alumni_id)}>{saved ? <Check size={15} /> : "+"}</button></div><span className="match-badge">{alum.match_score}% match</span><h3>{alum.name}</h3><p>{alum.current_role || "Industry Professional"} · {alum.company}</p><div className="match-reason">{alum.reason}</div><div className="card-actions"><button className="outline-button" onClick={() => requestMentorship(alum.alumni_id, alum.name)}><Send size={14} /> Mentor</button><button className="outline-button" onClick={() => requestConnection(alum.alumni_id, alum.name)}><Network size={14} /> Connect</button></div></article>;
}

function OpportunityRadar({ notify, profile = {} }) {
  const [filter, setFilter] = useState("All");
  const [query, setQuery] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const load = async () => {
    setLoading(true);
    try {
      const response = await API.get("/opportunities");
      setItems(response.data.map((item, index) => ({ ...item, company: item.organization, accent: ["violet", "orange", "cyan"][index % 3] })));
    } catch {
      setItems(opportunities.map((item, index) => ({ ...item, id: `demo-${index}`, fit_score: 45, matching_skills: [], saved: false })));
      notify("Using the demo opportunity signal while the API reconnects.");
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const filtered = items.filter((item) => (filter === "All" || item.type === filter) && `${item.title} ${item.company} ${item.location} ${(item.skills || []).join(" ")}`.toLowerCase().includes(query.toLowerCase()));
  const toggleSave = async (item) => {
    if (String(item.id).startsWith("demo-")) return notify("Demo cards become saveable when the API is running.");
    try {
      const response = item.saved ? await API.delete(`/opportunities/${item.id}/save`) : await API.post(`/opportunities/${item.id}/save`);
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, saved: response.data.saved } : entry));
      notify(response.data.message);
    } catch (error) { notify(error.response?.data?.detail || "Unable to update your launch list."); }
  };
  return <div className="view-stack"><div className="page-intro"><div><span className="eyebrow">LIVE SIGNALS · PROFILE-AWARE RADAR</span><h1>Opportunity radar</h1><p>Openings ranked by your actual skills, projects and target direction.</p></div><button className="primary-button compact" onClick={load}><Zap size={15} /> Refresh radar</button></div><div className="radar-controls"><div className="radar-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search roles, companies or skills..." /></div><div className="filter-row">{["All", "Internship", "Challenge", "Fellowship"].map((item) => <button className={filter === item ? "selected" : ""} key={item} onClick={() => setFilter(item)}>{item}</button>)}</div></div>{loading ? <div className="empty-chat">Calibrating your opportunity signal...</div> : <div className="opportunity-grid">{filtered.map((item) => <article className={`opportunity-card ${item.accent}`} key={item.id}><div className="opportunity-meta"><span>{item.type}</span><span>{item.deadline}</span></div><div className="company-logo">{item.company.charAt(0)}</div><div className="opportunity-fit"><span>{item.fit_score}% fit</span>{item.matching_skills?.length > 0 && <small>{item.matching_skills.length} skill match{item.matching_skills.length > 1 ? "es" : ""}</small>}</div><h2>{item.title}</h2><p>{item.company} · {item.location}</p><div className="tag-row">{item.skills.map((skill) => <span className={item.matching_skills?.includes(skill) ? "matched-tag" : ""} key={skill}>{skill}</span>)}</div><p className="opportunity-description">{item.description}</p><div className="opportunity-actions"><button className="text-button light" onClick={() => toggleSave(item)}>{item.saved ? <><Check size={15} /> Saved to launch list</> : <>Save to launch list <ArrowUpRight size={15} /></>}</button>{item.link && <a className="text-button light" href={item.link} target="_blank" rel="noreferrer">Open mission <ArrowUpRight size={15} /></a>}</div></article>)}</div>}{!loading && filtered.length === 0 && <div className="empty-chat">No opportunities match this orbit. Try another skill, company or category.</div>}</div>;
}

function NetworkView({ recommendations, savedAlumni, toggleSaved, requestMentorship, requestConnection }) {
  return <div className="view-stack"><div className="page-intro"><div><span className="eyebrow">YOUR HUMAN GRAPH</span><h1>Alumni network</h1><p>Relationships compound. Start with the people already close to your path.</p></div><div className="network-count"><Network size={19} /><strong>{recommendations.length}</strong><span>reachable alumni</span></div></div><div className="network-map"><div className="map-center"><div className="avatar xl">R</div><span>You</span></div>{recommendations.concat(recommendations).slice(0, 6).map((alum, index) => <div key={`${alum.alumni_id}-${index}`} className={`map-node node-${index}`}><div className="avatar">{alum.name?.charAt(0)}</div><span>{alum.name?.split(" ")[0]}</span></div>)}<div className="map-line line-1" /><div className="map-line line-2" /><div className="map-line line-3" /><div className="map-line line-4" /></div><div className="section-heading"><div><span className="eyebrow muted">PEOPLE TO KNOW</span><h2>Recommended introductions</h2></div></div><div className="mentor-grid">{recommendations.map((alum) => <MentorCard key={alum.alumni_id} alum={alum} saved={savedAlumni.includes(alum.alumni_id)} toggleSaved={toggleSaved} requestMentorship={requestMentorship} requestConnection={requestConnection} />)}</div></div>;
}

function AdminOverview({ analytics }) {
  const summary = analytics?.summary || {};
  const students = analytics?.students || [];
  const alumni = analytics?.alumni || [];

  return <div className="view-stack">
    <div className="page-intro"><div><span className="eyebrow">ADMIN CONTROL</span><h1>Institutional directory</h1><p>Full student and alumni roster with work history, skills, projects, and profile signals.</p></div></div>
    <div className="stat-grid">
      <div className="stat-card"><span>TOTAL USERS</span><strong>{summary.total_users || students.length + alumni.length}</strong><small>{summary.total_students || students.length} students</small></div>
      <div className="stat-card"><span>STUDENT POPULATION</span><strong>{summary.total_students || students.length}</strong><small>{summary.total_alumni || alumni.length} alumni</small></div>
      <div className="stat-card"><span>SKILL SIGNALS</span><strong>{summary.total_skills || 0}</strong><small>{summary.active_connections || 0} active connections</small></div>
    </div>
    <div className="admin-grid">
      <section className="profile-panel admin-panel">
        <div className="section-heading"><div><span className="eyebrow muted">STUDENTS</span><h2>{students.length} full profiles</h2></div></div>
        <div className="admin-record-list">
          {students.map((student) => <div className="admin-record" key={student.user_id || student.email}><div className="avatar">{(student.name || student.email || "S").charAt(0).toUpperCase()}</div><div className="admin-record-body"><strong>{student.name || "Unnamed student"}</strong><small>{student.email || "No email"}</small><small>{student.branch || "Branch not set"} · {student.target_role || student.career_goal || "No target role"}</small><div className="admin-skill-list">{(student.skills || []).slice(0, 5).map((skill) => <span key={`${student.user_id}-${skill}`}>{skill}</span>)}</div></div></div>)}
        </div>
      </section>
      <section className="profile-panel admin-panel">
        <div className="section-heading"><div><span className="eyebrow muted">ALUMNI</span><h2>{alumni.length} full profiles</h2></div></div>
        <div className="admin-record-list">
          {alumni.map((profile) => <div className="admin-record" key={profile.user_id || profile.email}><div className="avatar">{(profile.name || profile.email || "A").charAt(0).toUpperCase()}</div><div className="admin-record-body"><strong>{profile.name || "Unnamed alumni"}</strong><small>{profile.email || "No email"}</small><small>{profile.company || "Company not set"} · {profile.current_role || "Role not set"}</small><div className="admin-skill-list">{(profile.skills || []).slice(0, 5).map((skill) => <span key={`${profile.user_id}-${skill}`}>{skill}</span>)}</div></div></div>)}
        </div>
      </section>
    </div>
  </div>;
}

function MessagesView({ connections, currentUserId, notify }) {
  const [selected, setSelected] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    if (!selected) return;
    API.get(`/connections/${selected.id}/messages`).then((response) => setMessages(response.data)).catch((error) => notify(error.response?.data?.detail || "Unable to load chat."));
  }, [selected, notify]);

  const send = async (event) => {
    event.preventDefault();
    if (!draft.trim() || !selected) return;
    try {
      const response = await API.post(`/connections/${selected.id}/messages`, { message: draft });
      setMessages((current) => [...current, response.data]);
      setDraft("");
    } catch (error) {
      notify(error.response?.data?.detail || "Unable to send message.");
    }
  };

  const accepted = connections.filter((connection) => connection.status === "Connected");
  return <div className="view-stack">
    <div className="page-intro"><div><span className="eyebrow">PRIVATE CONVERSATIONS</span><h1>Messages</h1><p>Chat is available after a connection request is accepted.</p></div></div>
    <div className="chat-layout">
      <aside className="chat-list">{connections.length === 0 && <div className="empty-chat">No connection requests yet.</div>}{connections.map((connection) => <button key={connection.id} className={`chat-contact ${selected?.id === connection.id ? "selected" : ""}`} onClick={() => setSelected(connection)}><div className="avatar">{connection.name?.charAt(0)}</div><div><strong>{connection.name}</strong><small>{connection.status === "Connected" ? "Connected · Chat available" : `Request ${connection.status.toLowerCase()}`}</small></div><span className={`status-dot ${connection.status.toLowerCase()}`} /></button>)}</aside>
      <section className="chat-window">{!selected && <div className="empty-chat large-empty"><MessageSquare size={28} /><h2>Select a connection</h2><p>Accept a connection request to start a private conversation.</p></div>}{selected && selected.status !== "Connected" && <div className="empty-chat large-empty"><MessageSquare size={28} /><h2>Connection {selected.status.toLowerCase()}</h2><p>Chat unlocks when the alumni accepts the request.</p></div>}{selected?.status === "Connected" && <><div className="chat-header"><div className="avatar">{selected.name?.charAt(0)}</div><div><strong>{selected.name}</strong><small>{selected.role === "ALUMNI" ? "Alumni connection" : "Student connection"}</small></div></div><div className="message-list">{messages.length === 0 && <div className="empty-chat">No messages yet. Start the conversation.</div>}{messages.map((message) => <div key={message.id} className={`message-bubble ${message.sender_id === currentUserId ? "mine" : ""}`}>{message.message}<small>{new Date(message.created_at).toLocaleString()}</small></div>)}</div><form className="chat-composer" onSubmit={send}><input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Write a thoughtful message..." maxLength={2000} /><button className="primary-button compact" type="submit"><Send size={15} /> Send</button></form></>}</section>
    </div>
  </div>;
}

function StudentRequests({ connections = [], notify }) {
  const [mentorships, setMentorships] = useState([]);
  useEffect(() => {
    API.get("/mentorship/requests")
      .then((response) => setMentorships(response.data))
      .catch((error) => notify(error.response?.data?.detail || "Unable to load mentorship requests."));
  }, [notify]);
  return <div className="view-stack"><div className="page-intro"><div><span className="eyebrow">OUTBOUND SIGNALS</span><h1>My requests</h1><p>Track alumni connection and mentorship requests from one place.</p></div></div><section className="request-panel"><h2>Alumni connections</h2>{connections.length === 0 && <div className="empty-chat">You have not sent an alumni connection request yet. Open Alumni network to get started.</div>}{connections.map((item) => <div className="request-row" key={item.id}><div className="avatar">{item.name?.charAt(0) || "A"}</div><div><strong>{item.name}</strong><small>Alumni connection request</small></div><span className={`request-status ${item.status.toLowerCase()}`}>{item.status}</span></div>)}</section><section className="request-panel"><h2>Mentorship requests</h2>{mentorships.length === 0 && <div className="empty-chat">No mentorship requests yet.</div>}{mentorships.map((item) => <div className="request-row" key={item.id}><div className="avatar"><Send size={15} /></div><div><strong>{item.skill}</strong><small>{item.message || "Mentorship request"}</small></div><span className={`request-status ${item.status.toLowerCase()}`}>{item.status}</span></div>)}</section></div>;
}

function AlumniRequests({ notify, refreshConnections }) {
  const [connections, setConnections] = useState([]);
  const [mentorships, setMentorships] = useState([]);
  const load = async () => {
    try {
      const [connectionResponse, mentorshipResponse] = await Promise.all([API.get("/connections"), API.get("/mentorship/requests")]);
      setConnections(connectionResponse.data.filter((item) => item.status === "Pending"));
      setMentorships(mentorshipResponse.data.filter((item) => item.status === "Pending"));
    } catch (error) {
      notify(error.response?.data?.detail || "Unable to load requests.");
    }
  };
  useEffect(() => { load(); }, []);
  const respond = async (kind, id, action) => {
    try {
      await API.put(`/${kind}/${id}/${action}`);
      notify(`${kind === "connections" ? "Connection" : "Mentorship"} ${action}ed`);
      await load();
      if (kind === "connections") refreshConnections();
    } catch (error) {
      notify(error.response?.data?.detail || "Unable to update request.");
    }
  };
  return <div className="view-stack"><div className="page-intro"><div><span className="eyebrow">INBOX</span><h1>Requests</h1><p>Review people who want to learn from you and connect with you.</p></div></div><section className="request-panel"><h2>Connection requests</h2>{connections.length === 0 && <div className="empty-chat">No pending connection requests.</div>}{connections.map((item) => <div className="request-row" key={item.id}><div className="avatar">{item.name?.charAt(0)}</div><div><strong>{item.name}</strong><small>Wants to connect with you</small></div><div className="request-actions"><button className="outline-button" onClick={() => respond("connections", item.id, "accept")}>Accept</button><button className="outline-button" onClick={() => respond("connections", item.id, "reject")}>Reject</button></div></div>)}</section><section className="request-panel"><h2>Mentorship requests</h2>{mentorships.length === 0 && <div className="empty-chat">No pending mentorship requests.</div>}{mentorships.map((item) => <div className="request-row" key={item.id}><div className="avatar"><Send size={15} /></div><div><strong>{item.skill}</strong><small>{item.message}</small></div><div className="request-actions"><button className="outline-button" onClick={() => respond("mentorship", item.id, "accept")}>Accept</button><button className="outline-button" onClick={() => respond("mentorship", item.id, "reject")}>Reject</button></div></div>)}</section></div>;
}

function Toolkit({ notify, profile = {}, role }) {
  const profileResume = [
    profile.name, profile.bio, (profile.skills || []).join(", "),
    (profile.projects || []).join(". "), (profile.interests || []).join(", "),
    profile.location
  ].filter(Boolean).join(". ");
  const profileTarget = profile.target_role || profile.career_goal || profile.current_role || "Software Engineer";
  const [resume, setResume] = useState(profileResume);
  const [job, setJob] = useState(`Target role: ${profileTarget}. Required skills include problem solving, software delivery, collaboration, and production-ready engineering.`);
  const [result, setResult] = useState(null);
  const [placement, setPlacement] = useState(null);
  const [whatIfSkill, setWhatIfSkill] = useState("");
  const [whatIfResult, setWhatIfResult] = useState(null);
  useEffect(() => {
    setResume(profileResume);
    setJob(`Target role: ${profileTarget}. Required skills include problem solving, software delivery, collaboration, and production-ready engineering.`);
  }, [profile.name, profileTarget, (profile.skills || []).join("|"), (profile.projects || []).join("|")]);
  const runMatch = async () => {
    if (!resume || !job) return notify("Add both sides of the signal first");
    try { const response = await API.post("/api/match-job", { resume_text: resume, job_description: job }); setResult(response.data); } catch (error) { notify(error.response?.data?.detail || "Unable to run the resonance scan."); }
  };
  const runPlacement = async () => {
    try { const response = await API.get("/career/readiness"); setPlacement(response.data); } catch (error) { notify(error.response?.data?.detail || "Unable to calculate your pulse."); }
  };
  const runWhatIf = async () => {
    if (!whatIfSkill.trim()) return notify("Enter a skill to explore its career orbit.");
    try { const response = await API.post("/career/what-if", { new_skill: whatIfSkill.trim() }); setWhatIfResult(response.data); } catch (error) { notify(error.response?.data?.detail || "Unable to run the career simulation."); }
  };
  return <div className="view-stack"><div className="page-intro"><div><span className="eyebrow">PRIVATE INTELLIGENCE LAYER</span><h1>AI toolkit</h1><p>Turn your ambition into a measurable next move.</p></div></div><div className="tool-grid"><section className="tool-card"><div className="tool-heading"><div className="tool-icon purple"><Sparkles size={19} /></div><div><span className="eyebrow">ROLE FIT</span><h2>Resume resonance</h2></div></div><p>Your scan starts from your saved profile. Tune either side to explore a different path.</p><textarea value={resume} onChange={(event) => setResume(event.target.value)} placeholder="Your profile story..." /><textarea value={job} onChange={(event) => setJob(event.target.value)} placeholder="Target role or job description..." /><button className="primary-button compact" onClick={runMatch}>Run resonance scan <ArrowUpRight size={15} /></button>{result && <div className="tool-result"><strong>{result.match_score}%</strong><span>{result.feedback}</span></div>}</section><section className="tool-card placement-tool"><div className="tool-heading"><div className="tool-icon orange"><CircleGauge size={19} /></div><div><span className="eyebrow">READINESS MODEL</span><h2>Placement pulse</h2></div></div><p>Transparent estimate from the signals you control—not a promise of placement.</p><div className="pulse-score"><strong>{placement?.placement_probability ?? "—"}<small>%</small></strong><span>placement probability</span></div><div className="pulse-factors"><span><Check size={13} /> GPA signal {placement && `${placement.signals.gpa}%`}</span><span><Check size={13} /> Portfolio depth {placement && `${placement.signals.portfolio}%`}</span><span><Check size={13} /> Coding signal {placement && `${placement.signals.coding}%`}</span></div><button className="outline-button" onClick={runPlacement}>Calculate my pulse <TrendingUp size={15} /></button>{placement && <><div className="status-note">{placement.status}</div><div className="next-moves">{placement.next_moves.map((move) => <span key={move}>→ {move}</span>)}</div></>}</section></div><section className="tool-card time-machine-card"><div className="tool-heading"><div className="tool-icon cyan"><Target size={19} /></div><div><span className="eyebrow">CAREER TIME MACHINE</span><h2>What if I learn...</h2></div></div><p>Test a future skill against the real alumni career graph. See where it can take you before investing your time.</p><div className="time-machine-input"><input value={whatIfSkill} onChange={(event) => setWhatIfSkill(event.target.value)} onKeyDown={(event) => event.key === "Enter" && runWhatIf()} placeholder="e.g. Kubernetes, Product Analytics, GenAI" /><button className="primary-button compact" onClick={runWhatIf}>Simulate orbit <ArrowUpRight size={15} /></button></div>{whatIfResult && <div className="what-if-result"><div className="what-if-head"><strong>{whatIfResult.comparable_alumni_count}</strong><span>alumni paths found for <b>{whatIfResult.new_skill}</b></span></div><div className="what-if-columns"><div><small>ADJACENT SKILLS</small><div className="profile-chips">{(whatIfResult.common_co_skills || []).slice(0, 6).map((skill) => <span key={skill}>{skill}</span>)}</div></div><div><small>LIKELY ROLES</small><div className="profile-chips">{(whatIfResult.related_roles || []).slice(0, 5).map((item) => <span key={item}>{item}</span>)}</div></div></div><div className="what-if-people">{(whatIfResult.comparable_alumni || []).slice(0, 3).map((person) => <span key={`${person.name}-${person.company}`}>{person.name} · {person.company}</span>)}</div></div>}</section></div>;
}

export default App;
