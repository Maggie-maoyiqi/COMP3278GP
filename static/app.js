const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const app = $("#app");
const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[char]));
const fmt = value => value ? new Intl.DateTimeFormat("zh-HK", {
  dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Hong_Kong"
}).format(new Date(value)) : "—";
const dateOnly = value => value ? value.slice(0, 10) : "—";
const isOverdue = value => value && new Date(value) < new Date();
let me = null;
let currentPage = "catalog";

async function api(path, method = "GET", data) {
  const response = await fetch("/api/" + path, {
    method,
    headers: {"Content-Type": "application/json"},
    body: data === undefined ? undefined : JSON.stringify(data)
  });
  const body = await response.json();
  if (!response.ok) {
    const error = new Error(body.error || "Request failed.");
    error.status = response.status;
    throw error;
  }
  return body;
}

function toast(message, error = false) {
  const element = document.createElement("div");
  element.className = "toast" + (error ? " error-toast" : "");
  element.textContent = message;
  $("#toastRegion").append(element);
  setTimeout(() => element.remove(), 3800);
}

function login() {
  let role = "student";
  app.innerHTML = `
    <main class="login-page">
      <section class="login-visual">
        <div class="university-mark">
          <div class="crest">HKU</div>
          <div><strong>The University of Hong Kong</strong><small>LIBRARIES · SMART LIBRARY PORTAL</small></div>
        </div>
        <div class="hero-copy">
          <div class="kicker">KNOWLEDGE FOR ALL</div>
          <h1>Discover knowledge.<br>Start here.</h1>
          <p>Search the collection, manage your loans and requests, and connect with HKU's academic resources.</p>
        </div>
        <div class="login-quote">“Sapientia et Virtus” · Wisdom and Virtue</div>
      </section>
      <section class="login-side">
        <form class="login-card" id="loginForm">
          <div class="eyebrow">Library Account</div>
          <h2>Welcome back</h2>
          <p>Select your role and sign in to the library portal.</p>
          <div class="role-switch">
            <button type="button" data-role="student" class="active">Student</button>
            <button type="button" data-role="admin">Librarian</button>
          </div>
          <label class="field">Email<input name="email" type="email" autocomplete="email" value="kayan.chan@connect.hku.hk" required></label>
          <label class="field">Password<input name="password" type="password" autocomplete="current-password" value="Student123!" required></label>
          <p class="error" id="loginError" role="alert"></p>
          <button class="primary wide">Sign in</button>
          <div class="demo-box">
            Student demo: kayan.chan@connect.hku.hk / Student123!<br>
            Librarian demo: librarian@connect.hku.hk / Librarian123!
          </div>
        </form>
      </section>
    </main>`;
  $$("[data-role]").forEach(button => button.onclick = () => {
    role = button.dataset.role;
    $$("[data-role]").forEach(item => item.classList.toggle("active", item === button));
    const form = $("#loginForm");
    form.email.value = role === "student" ? "kayan.chan@connect.hku.hk" : "librarian@connect.hku.hk";
    form.password.value = role === "student" ? "Student123!" : "Librarian123!";
  });
  $("#loginForm").onsubmit = async event => {
    event.preventDefault();
    $("#loginError").textContent = "";
    try {
      me = await api("login", "POST", {
        email: event.target.email.value.trim(),
        password: event.target.password.value,
        role
      });
      me = await api("me");
      route(me.role === "student" ? "catalog" : "dashboard");
    } catch (error) {
      $("#loginError").textContent = error.message;
    }
  };
}

const studentNav = [
  ["catalog", "⌕", "Search"],
  ["loans", "▤", "My Loans"],
  ["study-rooms", "⌂", "Study Room Booking"],
  ["bookings", "▦", "My Bookings"],
  ["reservations", "◷", "My Requests"]
];
const adminNav = [
  ["dashboard", "⌂", "Overview"],
  ["circulation", "⇄", "Circulation"],
  ["books", "▦", "Books"],
  ["copies", "▥", "Copies"],
  ["students", "♙", "Students"],
  ["reservations", "◷", "Requests"]
];

function pageTitle(key) {
  const names = {
    catalog: "Library Search", loans: "My Loans", bookings: "My Bookings", "study-rooms": "Study Room Booking", reservations: me.role === "admin" ? "Request Queue" : "My Requests",
    dashboard: "Librarian Overview", circulation: "Circulation Desk", books: "Book Records", copies: "Physical Copies",
    students: "Student Accounts", account: "My Account"
  };
  return names[key] || "Library Portal";
}

function shell(content, active) {
  const nav = me.role === "student" ? studentNav : adminNav;
  const identity = me.role === "student" ? me.student.name : "Librarian";
  const sub = me.role === "student" ? me.student.student_no : me.username;
  app.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="side-brand"><div class="crest">HKU</div><div><strong>HKU Libraries</strong><small>SMART LIBRARY PORTAL</small></div></div>
        <nav class="side-nav">
          ${nav.map(([key, icon, label]) => `<button data-page="${key}" class="${active === key ? "active" : ""}"><span>${icon}</span><em>${label}</em></button>`).join("")}
          <button data-page="account" class="mobile-account ${active === "account" ? "active" : ""}"><span>♙</span><em>My Account</em></button>
        </nav>
        <div class="side-foot"><strong>${esc(identity)}</strong><span>${esc(sub)}</span><button class="account-link ${active === "account" ? "active" : ""}" id="accountLink">♙ <em>My Account</em></button><button class="logout" id="logout">Sign out</button></div>
      </aside>
      <section class="main-area">
        <header class="topbar"><h1>${pageTitle(active)}</h1><div class="meta"><strong>${esc(identity)}</strong>${me.role === "student" ? "Student account" : "Librarian account"}</div></header>
        <div class="content">${content}</div>
      </section>
    </div>`;
  $$("[data-page]").forEach(button => button.onclick = () => route(button.dataset.page));
  $("#accountLink").onclick = () => route("account");
  $("#logout").onclick = async () => {
    try { await api("logout", "POST", {}); } finally { me = null; login(); }
  };
}

async function route(page) {
  currentPage = page;
  try {
    if (page === "account") return accountPage();
    if (me.role === "student") {
      if (page === "catalog") return catalog();
      if (page === "loans") return studentLoans();
      if (page === "bookings") return studentBookings();
      if (page === "study-rooms") return studyRoomPage();
      if (page === "reservations") return studentReservations();
    } else {
      if (page === "dashboard") return adminDashboard();
      if (page === "circulation") return circulation();
      if (page === "books") return adminBooks();
      if (page === "copies") return adminCopies();
      if (page === "students") return adminStudents();
      if (page === "reservations") return adminReservations();
    }
  } catch (error) {
    if (error.status === 401) return login();
    toast(error.message, true);
  }
}

async function catalog(filters = {}) {
  const query = new URLSearchParams();
  if (filters.q) query.set("q", filters.q);
  if (filters.category) query.set("category", filters.category);
  if (filters.available) query.set("available", "1");
  const [data, overview] = await Promise.all([api("catalog?" + query), api("student/overview")]);
  shell(`
    <section class="hero-panel">
      <div><div class="eyebrow">DISCOVER THE COLLECTION</div><h2>Hello, ${esc(overview.student.name)}</h2><p>What would you like to read today? Explore ${data.books.length} matching titles.</p></div>
    </section>
    <div class="summary-row">
      <div class="stat"><div class="stat-icon">▤</div><b>${overview.active_loans}</b><span>Active loans</span></div>
      <div class="stat ${overview.overdue ? "warning" : ""}"><div class="stat-icon">!</div><b>${overview.overdue}</b><span>Overdue items</span></div>
      <div class="stat"><div class="stat-icon">◷</div><b>${overview.reservations}</b><span>Active requests</span></div>
      <div class="stat"><div class="stat-icon">♧</div><b>${overview.student.max_loans - overview.active_loans}</b><span>Loan slots available</span></div>
    </div>
    <div class="page-heading">
      <div><div class="eyebrow">Library Catalogue</div><h2>Search the collection</h2><p>Find titles by book name, author, or ISBN.</p></div>
      <form class="toolbar" id="searchForm">
        <input class="search-input" name="q" aria-label="Search the collection" placeholder="Title, author, or ISBN…" value="${esc(filters.q || "")}">
        <select name="category" aria-label="Category"><option value="">All categories</option>${data.categories.map(item => `<option value="${esc(item)}" ${item === filters.category ? "selected" : ""}>${esc(item)}</option>`).join("")}</select>
        <label><input type="checkbox" name="available" ${filters.available ? "checked" : ""}> Available only</label>
        <button class="primary">Search</button>
      </form>
    </div>
    <section class="book-grid">
      ${data.books.length ? data.books.map(bookCard).join("") : `<div class="empty-state"><div>⌕</div><b>No matching titles</b><span>Try a shorter keyword or clear the filters.</span></div>`}
    </section>`, "catalog");
  $("#searchForm").onsubmit = event => {
    event.preventDefault();
    catalog({
      q: event.target.q.value.trim(),
      category: event.target.category.value,
      available: event.target.available.checked
    });
  };
  $$("[data-book]").forEach(button => button.onclick = () => bookDetail(button.dataset.book));
}

function bookCard(book) {
  return `<article class="book-card">
    <div class="book-cover">${esc(book.title)}</div>
    <div class="book-info">
      <span class="category">${esc(book.category)}</span>
      <h3>${esc(book.title)}</h3>
      <div class="authors">${esc(book.authors)}</div>
      <div class="availability ${book.available_copies ? "" : "none"}"><i class="dot"></i>${book.available_copies ? `${book.available_copies} of ${book.total_copies} available` : `Unavailable · ${book.total_copies} copies`}</div>
      <button data-book="${book.id}">View details</button>
    </div>
  </article>`;
}

async function bookDetail(bookId) {
  const book = await api("books/" + bookId);
  const dialog = document.createElement("dialog");
  dialog.innerHTML = `<div class="modal">
    <div class="modal-head"><div><div class="eyebrow">${esc(book.category)}</div><h2>Book details</h2></div><button class="close" aria-label="Close">×</button></div>
    <div class="detail-layout">
      <div class="book-cover">${esc(book.title)}</div>
      <div><span class="category">ISBN ${esc(book.isbn)}</span><h2>${esc(book.title)}</h2><div class="authors">${esc(book.authors)}</div><p class="detail-description">${esc(book.description)}</p><p class="authors">${esc(book.publisher)} · ${book.publication_year} · ${esc(book.language)}</p></div>
    </div>
    <div class="copy-list"><h3>Physical copies</h3>
      ${book.copies.map(copy => `<div class="copy-row"><div><strong>${esc(copy.library_name)}</strong><br><span class="authors">${esc(copy.location)}</span></div><div>${esc(copy.shelf_location)}<br><span class="authors">${esc(copy.barcode)}</span></div><span class="status ${copy.status}">${statusLabel(copy.status)}</span></div>`).join("") || "<p class='authors'>No physical copies.</p>"}
    </div>
    ${me.role === "student" && !book.available_copies ? `<button class="primary wide" id="reserveBook">Join request queue</button>` : ""}
  </div>`;
  document.body.append(dialog);
  dialog.showModal();
  $(".close", dialog).onclick = () => dialog.remove();
  dialog.onclick = event => { if (event.target === dialog) dialog.remove(); };
  if ($("#reserveBook", dialog)) $("#reserveBook", dialog).onclick = async () => {
    try {
      await api("student/reservations", "POST", {book_id: book.id});
      toast("Request placed. You have joined the queue.");
      dialog.remove();
    } catch (error) { toast(error.message, true); }
  };
}

function statusLabel(status) {
  return ({available: "Available", borrowed: "On loan", reserved: "On hold", maintenance: "Maintenance", waiting: "Waiting", ready: "Ready for pickup", fulfilled: "Completed", cancelled: "Cancelled"})[status] || status;
}

async function studentLoans() {
  const loans = await api("student/loans");
  shell(`
    <div class="page-heading"><div><div class="eyebrow">My Library</div><h2>My loans</h2><p>Review due dates, renew current loans, and browse your history.</p></div></div>
    <section class="panel"><div class="panel-head"><h3>Loan history</h3><span class="authors">Up to 2 renewals, 14 days each</span></div>
      <div class="table-wrap"><table class="data-table"><thead><tr><th>Title</th><th>Barcode</th><th>Borrowed</th><th>Due / Returned</th><th>Status</th><th>Action</th></tr></thead>
      <tbody>${loans.map(loan => `<tr><td><strong>${esc(loan.title)}</strong><br><span class="authors">${esc(loan.library_name)}</span></td><td>${esc(loan.barcode)}</td><td>${dateOnly(loan.borrowed_at)}</td><td>${dateOnly(loan.returned_at || loan.due_at)}</td><td>${loan.returned_at ? '<span class="status returned">Returned</span>' : isOverdue(loan.due_at) ? '<span class="status overdue">Overdue</span>' : '<span class="status">On loan</span>'}</td><td>${!loan.returned_at ? `<button data-renew="${loan.id}" ${loan.renew_count >= 2 || isOverdue(loan.due_at) ? "disabled" : ""}>Renew · ${loan.renew_count}/2</button>` : "—"}</td></tr>`).join("") || `<tr><td colspan="6"><div class="empty-state"><b>No loan history</b></div></td></tr>`}</tbody></table></div>
    </section>`, "loans");
  $$("[data-renew]").forEach(button => button.onclick = async () => {
    try {
      const result = await api(`student/loans/${button.dataset.renew}/renew`, "POST", {});
      toast("Renewed. New due date: " + dateOnly(result.due_at));
      studentLoans();
    } catch (error) { toast(error.message, true); }
  });
}

async function studentReservations() {
  const rows = await api("student/reservations");
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Request Queue</div><h2>My requests</h2><p>Returned copies are held in request order.</p></div></div>
    <section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>Title</th><th>Requested</th><th>Queue position</th><th>Status</th><th>Action</th></tr></thead>
    <tbody>${rows.map(row => `<tr><td><strong>${esc(row.title)}</strong><br><span class="authors">${esc(row.isbn)}</span></td><td>${fmt(row.queued_at)}</td><td>${row.status === "waiting" ? "#" + row.queue_position : "—"}</td><td><span class="status ${row.status}">${statusLabel(row.status)}</span></td><td>${["waiting","ready"].includes(row.status) ? `<button class="danger-link" data-cancel="${row.id}">Cancel request</button>` : "—"}</td></tr>`).join("") || `<tr><td colspan="5"><div class="empty-state"><b>No requests</b><span>When a book has no available copies, request it from the book details.</span></div></td></tr>`}</tbody></table></div></section>`, "reservations");
  $$("[data-cancel]").forEach(button => button.onclick = async () => {
    if (!confirm("Cancel this request?")) return;
    try { await api("student/reservations/" + button.dataset.cancel, "DELETE"); toast("Request cancelled."); studentReservations(); }
    catch (error) { toast(error.message, true); }
  });
}

async function adminDashboard() {
  const stats = await api("admin/dashboard");
  shell(`
    <section class="hero-panel"><div><div class="eyebrow">LIBRARIAN WORKSPACE</div><h2>Good morning, Librarian</h2><p>Your collection and circulation activity at a glance.</p></div></section>
    <div class="summary-row">
      <div class="stat"><div class="stat-icon">▦</div><b>${stats.books}</b><span>Book records</span></div>
      <div class="stat"><div class="stat-icon">▥</div><b>${stats.copies}</b><span>Physical copies</span></div>
      <div class="stat"><div class="stat-icon">⇄</div><b>${stats.active_loans}</b><span>Active loans</span></div>
      <div class="stat warning"><div class="stat-icon">!</div><b>${stats.overdue}</b><span>Overdue loans</span></div>
    </div>
    <div class="split">
      <section class="panel"><div class="panel-head"><h3>Today's work</h3></div><div class="panel-body"><p><strong>${stats.reservations}</strong> active requests need attention.</p><button class="primary" id="goCirculation">Open circulation desk</button></div></section>
      <section class="panel"><div class="panel-head"><h3>Data model</h3></div><div class="panel-body"><p class="authors">A book record stores bibliographic data, while a copy stores its barcode and location. Loans reference copies; requests reference books.</p></div></section>
    </div>`, "dashboard");
  $("#goCirculation").onclick = () => route("circulation");
}

async function circulation() {
  const loans = await api("admin/loans?active=1");
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Circulation Desk</div><h2>Check out and return</h2><p>Scan or enter a student number and copy barcode.</p></div></div>
    <div class="split">
      <form class="form-card" id="checkoutForm"><h3>Check out a copy</h3><p>The system checks the loan limit, copy status, and request priority.</p>
        <label class="field">Student number<input name="student_no" placeholder="e.g. 3035000001" required></label>
        <label class="field">Copy barcode<input name="barcode" placeholder="e.g. HKU-DB-0001" required></label>
        <label class="field">Loan period<select name="loan_days"><option value="14">14 days</option><option value="30">30 days</option><option value="7">7 days</option></select></label>
        <p class="error" id="checkoutError"></p><button class="primary">Confirm checkout</button>
        <div class="note">Demo: student 3035000001 and copy HKU-DB-0001.</div>
      </form>
      <section class="panel"><div class="panel-head"><h3>Active loans</h3><span class="authors">${loans.length} records</span></div>
        <div class="table-wrap"><table class="data-table"><thead><tr><th>Student</th><th>Title / Barcode</th><th>Due date</th><th>Status</th><th>Action</th></tr></thead><tbody>
        ${loans.map(loan => `<tr><td><strong>${esc(loan.student_name)}</strong><br>${esc(loan.student_no)}</td><td>${esc(loan.title)}<br><span class="authors">${esc(loan.barcode)}</span></td><td>${dateOnly(loan.due_at)}</td><td>${isOverdue(loan.due_at) ? '<span class="status overdue">Overdue</span>' : '<span class="status">On loan</span>'}</td><td><button data-return="${loan.id}">Return</button></td></tr>`).join("")}
        </tbody></table></div></section>
    </div>`, "circulation");
  $("#checkoutForm").onsubmit = async event => {
    event.preventDefault(); $("#checkoutError").textContent = "";
    try {
      const result = await api("admin/checkout", "POST", {
        student_no: event.target.student_no.value.trim(),
        barcode: event.target.barcode.value.trim(),
        loan_days: Number(event.target.loan_days.value)
      });
      toast("Checked out. Due date: " + dateOnly(result.due_at));
      circulation();
    } catch (error) { $("#checkoutError").textContent = error.message; }
  };
  $$("[data-return]").forEach(button => button.onclick = async () => {
    if (!confirm("Confirm that this copy has been returned?")) return;
    try {
      const result = await api(`admin/loans/${button.dataset.return}/return`, "POST", {});
      toast(result.copy_status === "reserved" ? "Returned. The copy is now on hold for the next student." : "Return completed.");
      circulation();
    } catch (error) { toast(error.message, true); }
  });
}

async function adminBooks() {
  const books = await api("admin/books");
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Bibliographic Records</div><h2>Book records</h2><p>Maintain ISBN, title, author, and publication details.</p></div><button class="primary" id="addBook">＋ Add book</button></div>
    <section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>ID</th><th>Title</th><th>Authors</th><th>ISBN</th><th>Category</th><th>Copies</th><th>Action</th></tr></thead><tbody>
    ${books.map(book => `<tr><td>#${book.id}</td><td><strong>${esc(book.title)}</strong><br><span class="authors">${book.publication_year} · ${esc(book.publisher)}</span></td><td>${esc(book.authors)}</td><td>${esc(book.isbn)}</td><td>${esc(book.category)}</td><td>${book.available_copies} / ${book.total_copies} available</td><td><button data-edit-book="${book.id}">Edit</button> <button class="danger-link" data-delete-book="${book.id}">Delete</button></td></tr>`).join("")}</tbody></table></div></section>`, "books");
  $("#addBook").onclick = () => bookEditor();
  $$("[data-edit-book]").forEach(button => button.onclick = () => bookEditor(books.find(book => book.id == button.dataset.editBook)));
  $$("[data-delete-book]").forEach(button => button.onclick = async () => {
    if (!confirm("Only book records without copies can be deleted. Continue?")) return;
    try { await api("admin/books/" + button.dataset.deleteBook, "DELETE"); toast("Book record deleted."); adminBooks(); }
    catch (error) { toast(error.message, true); }
  });
}

function bookEditor(book = {}) {
  const dialog = document.createElement("dialog");
  dialog.innerHTML = `<form class="modal" id="bookForm"><div class="modal-head"><h2>${book.id ? "Edit" : "Add"} book record</h2><button type="button" class="close">×</button></div>
    <div class="form-grid">
      ${field("isbn", "ISBN", book.isbn, true)}
      ${field("publication_year", "Publication year", book.publication_year || new Date().getFullYear(), true, "number")}
      <div class="full">${field("title", "Title", book.title, true)}</div>
      <div class="full">${field("subtitle", "Subtitle", book.subtitle)}</div>
      <div class="full">${field("authors", "Authors (separate multiple names with commas)", book.authors, true)}</div>
      ${field("publisher", "Publisher", book.publisher, true)}
      ${field("category", "Category", book.category || "Computer Science", true)}
      ${field("language", "Language", book.language || "English", true)}
      ${field("cover_url", "Cover URL", book.cover_url)}
      <label class="field full">Description<textarea name="description" rows="4">${esc(book.description || "")}</textarea></label>
    </div><p class="error"></p><button class="primary wide">Save book</button></form>`;
  document.body.append(dialog); dialog.showModal();
  $(".close", dialog).onclick = () => dialog.remove();
  $("#bookForm", dialog).onsubmit = async event => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.target));
    body.publication_year = Number(body.publication_year);
    body.authors = body.authors.split(",").map(item => item.trim()).filter(Boolean);
    try {
      await api("admin/books" + (book.id ? "/" + book.id : ""), book.id ? "PUT" : "POST", body);
      dialog.remove(); toast("Book record saved."); adminBooks();
    } catch (error) { $(".error", dialog).textContent = error.message; }
  };
}

function field(name, label, value = "", required = false, type = "text") {
  return `<label class="field">${label}<input name="${name}" type="${type}" value="${esc(value)}" ${required ? "required" : ""}></label>`;
}

async function adminCopies() {
  const [copies, books, libraries] = await Promise.all([api("admin/copies"), api("admin/books"), api("admin/libraries")]);
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Physical Holdings</div><h2>Physical copies</h2><p>Maintain barcodes, locations, shelf marks, and statuses.</p></div><button class="primary" id="addCopy">＋ Add copy</button></div>
    <section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>Barcode</th><th>Title</th><th>Library / Shelf</th><th>Status</th><th>Held for</th><th>Action</th></tr></thead><tbody>
    ${copies.map(copy => `<tr><td><strong>${esc(copy.barcode)}</strong></td><td>${esc(copy.title)}</td><td>${esc(copy.library_name)}<br><span class="authors">${esc(copy.shelf_location)}</span></td><td><span class="status ${copy.status}">${statusLabel(copy.status)}</span></td><td>${esc(copy.reserved_for || "—")}</td><td><button data-edit-copy="${copy.id}">Edit</button> <button class="danger-link" data-delete-copy="${copy.id}">Delete</button></td></tr>`).join("")}</tbody></table></div></section>`, "copies");
  $("#addCopy").onclick = () => copyEditor({}, books, libraries);
  $$("[data-edit-copy]").forEach(button => button.onclick = () => copyEditor(copies.find(copy => copy.id == button.dataset.editCopy), books, libraries));
  $$("[data-delete-copy]").forEach(button => button.onclick = async () => {
    if (!confirm("Delete this copy? Copies with loan history cannot be deleted.")) return;
    try { await api("admin/copies/" + button.dataset.deleteCopy, "DELETE"); toast("Copy deleted."); adminCopies(); }
    catch (error) { toast(error.message, true); }
  });
}

function copyEditor(copy = {}, books, libraries) {
  const locked = ["borrowed", "reserved"].includes(copy.status);
  const dialog = document.createElement("dialog");
  dialog.innerHTML = `<form class="modal" id="copyForm"><div class="modal-head"><h2>${copy.id ? "Edit" : "Add"} copy</h2><button type="button" class="close">×</button></div>
    <label class="field">Book record<select name="book_id" required>${books.map(book => `<option value="${book.id}" ${book.id == copy.book_id ? "selected" : ""}>#${book.id} · ${esc(book.title)}</option>`).join("")}</select></label>
    <label class="field">Library<select name="library_id" required>${libraries.map(library => `<option value="${library.id}" ${library.id == copy.library_id ? "selected" : ""}>${esc(library.name)}</option>`).join("")}</select></label>
    ${field("barcode", "Copy barcode", copy.barcode, true)}
    ${field("shelf_location", "Shelf location", copy.shelf_location, true)}
    <label class="field">Status<select name="status" ${locked ? "disabled" : ""}><option value="available" ${copy.status !== "maintenance" ? "selected" : ""}>Available</option><option value="maintenance" ${copy.status === "maintenance" ? "selected" : ""}>Maintenance</option></select></label>
    ${field("acquired_at", "Acquisition date", copy.acquired_at || new Date().toISOString().slice(0, 10), true, "date")}
    ${locked ? '<p class="note">Use the circulation workflow to change a borrowed or reserved copy.</p>' : ""}
    <p class="error"></p><button class="primary wide" ${locked ? "disabled" : ""}>Save copy</button></form>`;
  document.body.append(dialog); dialog.showModal();
  $(".close", dialog).onclick = () => dialog.remove();
  $("#copyForm", dialog).onsubmit = async event => {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.target));
    body.book_id = Number(body.book_id); body.library_id = Number(body.library_id);
    try {
      await api("admin/copies" + (copy.id ? "/" + copy.id : ""), copy.id ? "PUT" : "POST", body);
      dialog.remove(); toast("Copy saved."); adminCopies();
    } catch (error) { $(".error", dialog).textContent = error.message; }
  };
}

async function adminStudents() {
  const students = await api("admin/students");
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Borrower Accounts</div><h2>Student accounts</h2><p>Review borrower profiles, account status, and active loans.</p></div></div>
    <section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>Student no.</th><th>Name</th><th>Email</th><th>Faculty</th><th>Loans / Limit</th><th>Account</th></tr></thead><tbody>
    ${students.map(student => `<tr><td><strong>${esc(student.student_no)}</strong></td><td>${esc(student.name)}<br><span class="authors">@${esc(student.username)}</span></td><td>${esc(student.email)}</td><td>${esc(student.faculty)}</td><td>${student.active_loans} / ${student.max_loans}</td><td><span class="status ${student.active ? "" : "cancelled"}">${student.active ? "Active" : "Inactive"}</span></td></tr>`).join("")}</tbody></table></div></section>`, "students");
}

async function adminReservations() {
  const rows = await api("admin/reservations");
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Hold Requests</div><h2>Request queue</h2><p>Review request order and pickup readiness.</p></div></div>
    <section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>Title</th><th>Student</th><th>Requested</th><th>Queue position</th><th>Status</th></tr></thead><tbody>
    ${rows.map(row => `<tr><td><strong>${esc(row.title)}</strong><br><span class="authors">${esc(row.isbn)}</span></td><td>${esc(row.student_name)}<br><span class="authors">${esc(row.student_no)}</span></td><td>${fmt(row.queued_at)}</td><td>${row.status === "waiting" ? "#" + row.queue_position : "—"}</td><td><span class="status ${row.status}">${statusLabel(row.status)}</span></td></tr>`).join("")}</tbody></table></div></section>`, "reservations");
}

async function accountPage() {
  const isStudent = me.role === "student";
  const name = isStudent ? me.student.name : "Librarian";
  const details = isStudent ? [
    ["Student number", me.student.student_no],
    ["Email", me.student.email],
    ["Faculty", me.student.faculty],
    ["Loan limit", me.student.max_loans + " items"]
  ] : [
    ["Username", me.username],
    ["Role", "Librarian"],
    ["Access", "Catalog, circulation, records, and borrower accounts"]
  ];
  shell(`
    <div class="page-heading"><div><div class="eyebrow">Profile & Session</div><h2>My Account</h2><p>Review the identity currently active in this browser.</p></div></div>
    <div class="split">
      <section class="panel"><div class="panel-body">
        <div class="profile-mark">${esc(name.split(" ").map(part => part[0]).join("").slice(0, 2))}</div>
        <h2 class="profile-name">${esc(name)}</h2>
        <p class="authors">@${esc(me.username)} · ${isStudent ? "Student" : "Librarian"}</p>
        <span class="status">${isStudent ? "Student account" : "Librarian account"}</span>
        <button class="danger-button account-signout" id="accountLogout">Sign out</button>
      </div></section>
      <section class="panel"><div class="panel-head"><h3>Account details</h3></div><div class="panel-body">
        <dl class="account-details">${details.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>
        ${!isStudent ? `<div class="account-switch"><div><strong>Test the student experience</strong><p>Open the fixed student demo account without returning to the sign-in page.</p></div><button class="primary" id="switchStudent">Switch to Student View</button></div>` : `<div class="note">To return to the librarian workspace, sign out and use the librarian demo credentials.</div>`}
      </div></section>
    </div>`, "account");
  if ($("#switchStudent")) $("#switchStudent").onclick = async () => {
    try {
      await api("demo/switch-to-student", "POST", {});
      me = await api("me");
      toast("Switched to the student demo account.");
      route("catalog");
    } catch (error) {
      toast(error.message, true);
    }
  };
  $("#accountLogout").onclick = async () => {
    try { await api("logout", "POST", {}); } finally { me = null; login(); }
  };
}

async function studyRoomPage() {
  const data = await api("student/study-room-slots");
  shell(`<div class="page-heading"><div><div class="eyebrow">Facilities</div><h2>Study room booking</h2><p>Choose an available one-hour slot. Each student may book up to two hours per day.</p></div></div><section class="panel" id="studyRoomPanel"></section>`, "study-rooms");
  const panel = $("#studyRoomPanel");
  const render = current => {
    const day = new Date(current.date + "T12:00:00");
    const label = new Intl.DateTimeFormat("en-HK", {weekday: "short", month: "short", day: "numeric"}).format(day);
    const tomorrow = new Date(day); tomorrow.setDate(day.getDate() + 1);
    const tomorrowDate = tomorrow.toISOString().slice(0, 10);
    panel.innerHTML = `<div class="panel-head"><div><h3>${label}</h3><span class="authors">8 rooms · 08:00–22:00 · one-hour slots</span></div><span class="status">Maximum 2 hours per day</span></div><div class="panel-body"><div class="study-room-toolbar"><strong>${label}</strong><div><button class="date-tab ${current.date === data.date ? "active" : ""}" data-room-date="${data.date}">Today</button><button class="date-tab ${current.date === tomorrowDate ? "active" : ""}" data-room-date="${tomorrowDate}">Tomorrow</button></div></div><div class="study-room-legend"><span><i class="legend-box available"></i>Available</span><span><i class="legend-box booked"></i>Booked</span><span><i class="legend-box expired"></i>Expired</span></div><div class="study-room-table"><div class="room-table-head"><span>Room</span>${Array.from({length: 14}, (_, index) => { const hour = index + 8; return `<span>${String(hour).padStart(2, "0")}:00</span>`; }).join("")}</div>${Array.from({length: 8}, (_, index) => { const room = index + 1; return `<div class="room-table-row"><strong>Room ${room}</strong>${current.slots.filter(slot => slot.room_no === room).map(slot => `<button class="room-cell ${slot.status}" data-room-slot="${slot.id}" ${slot.status === "available" ? "" : "disabled"} title="${slot.status === "available" ? "Book this hour" : slot.status === "booked" ? "Booked" : "Expired"}"></button>`).join("")}</div>`; }).join("")}</div><p class="authors room-note">Only green available slots can be selected. The schedule runs from 08:00 to 22:00; a confirmation is required before booking.</p></div>`;
    $$('[data-room-date]', panel).forEach(button => button.onclick = async () => render(await api("student/study-room-slots?date=" + button.dataset.roomDate)));
    $$('[data-room-slot]', panel).forEach(button => button.onclick = () => confirmRoomBooking(button.dataset.roomSlot, current));
  };
  render(data);
}

async function confirmRoomBooking(slotId, data) {
  const slot = data.slots.find(item => String(item.id) === String(slotId));
  if (!slot) return;
  const dialog = document.createElement("dialog");
  const start = new Date(slot.slot_start + "+08:00");
  const end = new Date(start.getTime() + 60 * 60 * 1000);
  const time = value => new Intl.DateTimeFormat("en-HK", {dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Hong_Kong"}).format(value);
  dialog.innerHTML = `<form method="dialog" class="modal"><div class="modal-head"><h2>Confirm booking</h2><button type="button" class="close">×</button></div><p>Are you sure to book <strong>Room ${slot.room_no}</strong> from <strong>${time(start)}</strong> to <strong>${time(end)}</strong>?</p><div class="modal-actions"><button value="cancel">Cancel</button><button class="primary" value="confirm">Confirm booking</button></div><p class="error"></p></form>`;
  document.body.append(dialog); dialog.showModal();
  $(".close", dialog).onclick = () => dialog.remove();
  $("form", dialog).onsubmit = async event => {
    event.preventDefault();
    if (event.submitter?.value !== "confirm") return dialog.remove();
    try { await api(`student/study-room-slots/${slot.id}/reserve`, "POST", {}); dialog.remove(); toast("Study-room hour reserved."); studyRoomPage(); }
    catch (error) { $(".error", dialog).textContent = error.message; }
  };
}

async function studentBookings() {
  const data = await api("student/study-room-bookings");
  shell(`<div class="page-heading"><div><div class="eyebrow">Facilities</div><h2>My Bookings</h2><p>Your upcoming study-room reservations.</p></div></div><section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>Room</th><th>Start</th><th>End</th><th>Status</th></tr></thead><tbody>${data.bookings.length ? data.bookings.map(row => { const end = new Date(new Date(row.slot_start).getTime() + 3600000); return `<tr><td><strong>Room ${row.room_no}</strong></td><td>${fmt(row.slot_start)}</td><td>${fmt(end.toISOString())}</td><td><span class="status">Booked</span></td></tr>`; }).join("") : `<tr><td colspan="4"><div class="empty-state"><b>No upcoming study-room bookings</b><span>Book a green available slot from Study Room Booking.</span></div></td></tr>`}</tbody></table></div></section>`, "bookings");
}

(async () => {
  try {
    me = await api("me");
    route(me.role === "student" ? "catalog" : "dashboard");
  } catch {
    login();
  }
})();
