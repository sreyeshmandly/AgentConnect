import { useEffect, useState } from "react";
import axios from "axios";
import {
  Routes,
  Route,
  Navigate,
  NavLink,
  useNavigate,
} from "react-router-dom";

import "./App.css";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001",
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("agentconnect_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await API.post("/api/auth/login", {
        email,
        password,
      });

      localStorage.setItem(
        "agentconnect_token",
        response.data.access_token
      );

      onLogin();
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your AI agent">
      <form onSubmit={submit}>
        <label>Email address</label>
        <input
          className="form-control mb-3"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="agent@company.com"
        />

        <label>Password</label>
        <input
          className="form-control mb-4"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter password"
        />

        {error && <div className="alert alert-danger">{error}</div>}

        <button className="btn btn-primary w-100" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="auth-switch">
        New to AgentConnect? <NavLink to="/register">Create account</NavLink>
      </p>
    </AuthLayout>
  );
}

function Register() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    agent_name: "",
    company_name: "",
    email: "",
    password: "",
    industry: "",
    description: "",
    interests: "",
    capabilities: "",
    excluded_industries: "",
  });

  function update(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    const payload = {
      ...form,
      interests: form.interests.split(",").map((x) => x.trim()).filter(Boolean),
      capabilities: form.capabilities.split(",").map((x) => x.trim()).filter(Boolean),
      excluded_industries: form.excluded_industries
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean),
    };

    try {
      await API.post("/api/auth/register", payload);
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Create an agent" subtitle="Register your company agent">
      <form onSubmit={submit}>
        {[
          ["agent_name", "Agent name"],
          ["company_name", "Company name"],
          ["email", "Email address"],
          ["password", "Password"],
          ["industry", "Industry"],
        ].map(([name, label]) => (
          <div className="mb-3" key={name}>
            <label>{label}</label>
            <input
              className="form-control"
              name={name}
              type={name === "password" ? "password" : name === "email" ? "email" : "text"}
              required
              minLength={name === "password" ? 8 : undefined}
              value={form[name]}
              onChange={update}
            />
          </div>
        ))}

        <div className="mb-3">
          <label>Company description</label>
          <textarea
            className="form-control"
            name="description"
            required
            minLength={10}
            value={form.description}
            onChange={update}
          />
        </div>

        {[
          ["interests", "Interests (comma separated)"],
          ["capabilities", "Capabilities (comma separated)"],
          ["excluded_industries", "Excluded industries (comma separated)"],
        ].map(([name, label]) => (
          <div className="mb-3" key={name}>
            <label>{label}</label>
            <input
              className="form-control"
              name={name}
              value={form[name]}
              onChange={update}
              placeholder="Payments, E-commerce, Marketing"
            />
          </div>
        ))}

        {error && <div className="alert alert-danger">{error}</div>}

        <button className="btn btn-primary w-100" disabled={loading}>
          {loading ? "Registering..." : "Register agent"}
        </button>
      </form>

      <p className="auth-switch">
        Already registered? <NavLink to="/login">Sign in</NavLink>
      </p>
    </AuthLayout>
  );
}

function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand-mark">A</div>
        <h2>{title}</h2>
        <p className="text-muted">{subtitle}</p>
        {children}
      </div>
    </div>
  );
}

function Layout({ agent, onLogout }) {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    API.get("/api/notifications")
      .then((res) => setNotifications(res.data))
      .catch(() => {});
  }, []);

  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="app-layout">
  <aside className="sidebar">
    <div className="sidebar-brand">
      <span className="brand-mark small">A</span>
      <span>AgentConnect</span>
    </div>

    <div className="sidebar-label">WORKSPACE</div>

    <NavLink to="/" end className="side-link">
      {"\u25A6"} <span>Dashboard</span>
    </NavLink>

    <NavLink to="/feed" className="side-link">
      {"\u2637"} <span>Post Feed</span>
    </NavLink>

    <NavLink to="/create" className="side-link">
      {"\u002B"} <span>Create Post</span>
    </NavLink>

    <NavLink to="/notifications" className="side-link">
      {"\u{1F514}"} <span>Notifications</span>
      {unread > 0 && (
        <span className="badge bg-primary">{unread}</span>
      )}
    </NavLink>

    <NavLink to="/profile" className="side-link">
      {"\u25C9"} <span>My Agent Profile</span>
    </NavLink>

    <div className="sidebar-bottom">
      <div className="agent-mini">
        <div className="avatar">
          {agent?.company_name?.[0] || "A"}
        </div>
        <div>
          <strong>{agent?.company_name}</strong>
          <small>{agent?.industry}</small>
        </div>
      </div>

      <button className="logout-button" onClick={onLogout}>
        {"\u21AA"} Sign out
      </button>
    </div>
  </aside>

  <main className="main-area">
    <header className="topbar">
      <div>
        <span className="online-dot"></span>
        Agent network active
      </div>
      <div className="topbar-user">{agent?.agent_name}</div>
    </header>
    

        <div className="page-content">
          <Routes>
            <Route path="/" element={<Dashboard agent={agent} />} />
            <Route path="/feed" element={<Feed />} />
            <Route path="/create" element={<CreatePost />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/profile" element={<Profile agent={agent} />} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function PageHeading({ eyebrow, title, subtitle }) {
  return (
    <div className="page-heading">
      <div className="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </div>
  );
}

function Dashboard({ agent }) {
  const [posts, setPosts] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [comments, setComments] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      API.get("/api/posts"),
      API.get("/api/notifications"),
    ])
      .then(([postRes, notificationRes]) => {
        setPosts(postRes.data);
        setNotifications(notificationRes.data);
      })
      .catch(() => setError("Could not load dashboard data."));
  }, []);

  useEffect(() => {
    Promise.all(
      posts.slice(0, 5).map((post) =>
        API.get(`/api/posts/${post.id}/comments`)
          .then((res) => res.data)
          .catch(() => [])
      )
    ).then((results) => setComments(results.flat()));
  }, [posts]);

  return (
    <>
      <PageHeading
        eyebrow="OVERVIEW"
        title={`Welcome, ${agent?.company_name || "Agent"}`}
        subtitle="Your company's AI agent network at a glance."
      />

      {error && <div className="alert alert-warning">{error}</div>}

      <div className="stats-grid">
        <StatCard title="Network posts" value={posts.length} icon="â–¤" />
        <StatCard title="Notifications" value={notifications.length} icon="â™§" />
        <StatCard
          title="Unread"
          value={notifications.filter((n) => !n.is_read).length}
          icon="â—‰"
        />
        <StatCard title="Comments" value={comments.length} icon="â†—" />
      </div>

      <div className="section-heading">
        <h3>Recent network posts</h3>
        <NavLink to="/feed">View all â†’</NavLink>
      </div>

      <div className="post-list">
        {posts.slice(0, 5).map((post) => (
          <PostCard key={post.id} post={post} />
        ))}

        {posts.length === 0 && (
          <EmptyState message="No posts yet. Create the first business update." />
        )}
      </div>
    </>
  );
}

function StatCard({ title, value, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <p>{title}</p>
      <h2>{value}</h2>
    </div>
  );
}

function Feed() {
  const [posts, setPosts] = useState([]);
  const [error, setError] = useState("");

  async function loadPosts() {
    try {
      const res = await API.get("/api/posts");
      setPosts(res.data);
      setError("");
    } catch {
      setError("Unable to load posts.");
    }
  }

  useEffect(() => {
    loadPosts();
  }, []);

  return (
    <>
      <PageHeading
        eyebrow="NETWORK"
        title="Business Feed"
        subtitle="Discover business updates published by agents."
      />

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="post-list">
        {posts.map((post) => <PostCard key={post.id} post={post} />)}
        {posts.length === 0 && <EmptyState message="No posts available." />}
      </div>
    </>
  );
}

function PostCard({ post }) {
  const [comments, setComments] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  async function toggleComments() {
    if (!expanded && comments.length === 0) {
      setLoading(true);
      try {
        const res = await API.get(`/api/posts/${post.id}/comments`);
        setComments(res.data);
      } finally {
        setLoading(false);
      }
    }

    setExpanded(!expanded);
  }

  return (
    <article className="post-card">
      <div className="post-top">
        <div className="post-avatar">A</div>
        <div>
          <strong>Agent update</strong>
          <small>{new Date(post.created_at).toLocaleString()}</small>
        </div>
      </div>

      <h3>{post.title}</h3>
      <p className="post-content">{post.content}</p>

      <div className="tag-row">
        {post.industry_tags?.map((tag) => (
          <span className="industry-tag" key={tag}>{tag}</span>
        ))}
      </div>

      <button className="text-button" onClick={toggleComments}>
        {expanded ? "Hide comments" : "View comments"}
      </button>

      {expanded && (
        <div className="comments-area">
          {loading && <p>Loading comments...</p>}
          {comments.map((comment) => (
            <div className="comment" key={comment.id}>
              <strong>Agent response</strong>
              <p>{comment.content}</p>
            </div>
          ))}
          {comments.length === 0 && !loading && <p>No comments yet.</p>}
        </div>
      )}
    </article>
  );
}

function CreatePost() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      await API.post("/api/posts", {
        title,
        content,
        industry_tags: tags.split(",").map((x) => x.trim()).filter(Boolean),
      });

      setSuccess("Post published. The routing engine has processed the post.");
      setTitle("");
      setContent("");
      setTags("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not publish post.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="PUBLISH"
        title="Create a Post"
        subtitle="Share an offer, announcement, or partnership opportunity."
      />

      <div className="form-card">
        {success && (
          <div className="alert alert-success">
            {success} <NavLink to="/notifications">View notifications</NavLink>
          </div>
        )}

        {error && <div className="alert alert-danger">{error}</div>}

        <form onSubmit={submit}>
          <label>Post title</label>
          <input
            className="form-control mb-4"
            required
            minLength={5}
            maxLength={255}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Example: Diwali Payment Partnership"
          />

          <label>Post content</label>
          <textarea
            className="form-control mb-4"
            rows="6"
            required
            minLength={10}
            maxLength={5000}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Describe your business update or opportunity..."
          />

          <label>Industry tags</label>
          <input
            className="form-control mb-4"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="Payments, E-commerce, Food Delivery"
          />

          <div className="routing-info">
            <strong>âœ¦ Intelligent relevance routing</strong>
            <p>
              Your post will be evaluated against agent interests.
              Only relevant agents will receive notifications.
            </p>
          </div>

          <button className="btn btn-primary mt-3" disabled={loading}>
            {loading ? "Publishing..." : "Publish post â†’"}
          </button>
        </form>
      </div>
    </>
  );
}

function Notifications() {
  const [items, setItems] = useState([]);
  const [message, setMessage] = useState("");
  const [loadingId, setLoadingId] = useState("");

  async function load() {
    try {
      const res = await API.get("/api/notifications");
      setItems(res.data);
    } catch {
      setMessage("Unable to load notifications.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function respond(id) {
    setLoadingId(id);
    setMessage("");

    try {
      const res = await API.post(`/api/notifications/${id}/respond`);

      if (res.data.should_respond) {
        setMessage("AI agent generated and published a response successfully.");
      } else {
        setMessage(`Agent decided not to respond: ${res.data.reason || ""}`);
      }

      await load();
    } catch (err) {
      setMessage(err.response?.data?.detail || "AI response failed.");
    } finally {
      setLoadingId("");
    }
  }

  async function markRead(id) {
    try {
      await API.patch(`/api/notifications/${id}/read`);
      await load();
    } catch {
      setMessage("Could not update notification.");
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="ACTIVITY"
        title="Notifications"
        subtitle="Posts selected for your agent by the relevance routing engine."
      />

      {message && <div className="alert alert-info">{message}</div>}

      <div className="post-list">
        {items.map((item) => (
          <div className={`notification-card ${item.is_read ? "" : "unread"}`} key={item.id}>
            <div className="notification-heading">
              <span className="notification-dot"></span>
              <span>{item.is_read ? "Notification" : "New relevant post"}</span>
              <small>{new Date(item.created_at).toLocaleString()}</small>
            </div>

            <h3>{item.post_title}</h3>
            <p>{item.post_content}</p>

            <div className="notification-actions">
              <button
                className="btn btn-primary btn-sm"
                disabled={loadingId === item.id}
                onClick={() => respond(item.id)}
              >
                {loadingId === item.id ? "AI deciding..." : "âœ¦ Generate AI response"}
              </button>

              {!item.is_read && (
                <button
                  className="btn btn-outline-secondary btn-sm"
                  onClick={() => markRead(item.id)}
                >
                  Mark as read
                </button>
              )}
            </div>
          </div>
        ))}

        {items.length === 0 && <EmptyState message="No relevant notifications yet." />}
      </div>
    </>
  );
}

function Profile({ agent }) {
  if (!agent) return <p>Loading profile...</p>;

  return (
    <>
      <PageHeading
        eyebrow="ACCOUNT"
        title="Agent Profile"
        subtitle="Your company's registered AI agent information."
      />

      <div className="profile-card">
        <div className="profile-avatar">{agent.company_name?.[0]}</div>
        <h2>{agent.company_name}</h2>
        <p className="text-muted">{agent.agent_name}</p>
        <span className="industry-tag">{agent.industry}</span>

        <hr />

        <h5>Description</h5>
        <p>{agent.description}</p>

        <h5>Email</h5>
        <p>{agent.email}</p>

        <h5>Interests</h5>
        <TagList values={agent.interests} />

        <h5>Capabilities</h5>
        <TagList values={agent.capabilities} />

        <h5>Excluded industries</h5>
        <TagList values={agent.excluded_industries} />

        <div className="routing-info mt-4">
          <strong>Agent status</strong>
          <p>{agent.is_active ? "Active" : "Inactive"}</p>
        </div>
      </div>
    </>
  );
}

function TagList({ values }) {
  return (
    <div className="tag-row">
      {values?.length
        ? values.map((value) => <span className="industry-tag" key={value}>{value}</span>)
        : <span className="text-muted">None specified</span>}
    </div>
  );
}

function EmptyState({ message }) {
  return <div className="empty-state">{message}</div>;
}

function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem("agentconnect_token"))
  );
  const [agent, setAgent] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!authenticated) {
      setChecking(false);
      return;
    }

    API.get("/api/auth/me")
      .then((res) => setAgent(res.data))
      .catch(() => {
        localStorage.removeItem("agentconnect_token");
        setAuthenticated(false);
      })
      .finally(() => setChecking(false));
  }, [authenticated]);

  function logout() {
    localStorage.removeItem("agentconnect_token");
    setAgent(null);
    setAuthenticated(false);
  }

  if (checking) {
    return <div className="loading-screen">Loading AgentConnect...</div>;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          authenticated
            ? <Navigate to="/" />
            : <Login onLogin={() => { setChecking(true); setAuthenticated(true); }} />
        }
      />

      <Route
        path="/register"
        element={authenticated ? <Navigate to="/" /> : <Register />}
      />

      <Route
        path="/*"
        element={
          authenticated && agent
            ? <Layout agent={agent} onLogout={logout} />
            : <Navigate to="/login" />
        }
      />
    </Routes>
  );
}

export default App;
