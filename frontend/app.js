// ====================
// CONFIGURAZIONE
// ====================
const IS_LOCAL = ['localhost', '127.0.0.1'].includes(location.hostname);
const API_BASE_URL = IS_LOCAL ? 'http://localhost:8000' : 'https://my-first-api-vtlr.onrender.com';

// ====================
// STATO
// ====================
let authToken = localStorage.getItem('authToken');
let userEmail = localStorage.getItem('userEmail');

// ====================
// ELEMENTI DOM
// ====================
const $ = (id) => document.getElementById(id);
const authSection = $('auth-section');
const appSection = $('app-section');
const loginForm = $('login-form');
const registerForm = $('register-form');
const authMessage = $('auth-message');
const todoForm = $('todo-form');
const todosContainer = $('todos-container');
const loadingElement = $('loading');
const tabButtons = document.querySelectorAll('.tab-btn');
const authForms = document.querySelectorAll('.auth-form');

// ====================
// UTILITY
// ====================
function showMessage(text, type = 'error') {
    authMessage.textContent = text;           // textContent: mai HTML
    authMessage.className = `auth-message ${type}`;
    authMessage.style.display = 'block';
    if (type === 'success') setTimeout(() => (authMessage.style.display = 'none'), 3000);
}

function setSession(token, email) {
    authToken = token;
    userEmail = email;
    try {
        if (token) {
            localStorage.setItem('authToken', token);
            localStorage.setItem('userEmail', email);
        } else {
            localStorage.removeItem('authToken');
            localStorage.removeItem('userEmail');
        }
    } catch (_) { /* storage non disponibile: la sessione dura solo finché la pagina è aperta */ }
}

function formatError(detail) {
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join('. ');
    return typeof detail === 'string' ? detail : null;
}

function makeIcon(classes) {
    const i = document.createElement('i');
    i.className = classes;
    return i;
}

function makeButton(className, iconClasses, label, onClick) {
    const b = document.createElement('button');
    b.className = className;
    b.type = 'button';
    b.append(makeIcon(iconClasses), ` ${label}`);
    b.addEventListener('click', onClick);
    return b;
}

// ====================
// API
// ====================
async function apiRequest(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;

    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
    } catch (_) {
        throw new Error('Server non raggiungibile. Se si sta avviando, riprova tra qualche secondo.');
    }

    if (response.status === 401 && authToken) {
        showAuthSection();
        throw new Error('Sessione scaduta, accedi di nuovo.');
    }
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(formatError(err.detail) || `Errore ${response.status}`);
    }
    if (response.status === 204) return null;
    return response.json();
}

const fetchTodosApi = () => apiRequest('/todos/');
const createTodoApi = (title, description) =>
    apiRequest('/todos/', { method: 'POST', body: JSON.stringify({ title, description: description || null }) });
const toggleTodoApi = (id, completed) =>
    apiRequest(`/todos/${id}`, { method: 'PUT', body: JSON.stringify({ completed }) });
const deleteTodoApi = (id) => apiRequest(`/todos/${id}`, { method: 'DELETE' });
const registerApi = (email, password) =>
    apiRequest('/register', { method: 'POST', body: JSON.stringify({ email, password }) });
const deleteAccountApi = (password) =>
    apiRequest('/me', { method: 'DELETE', body: JSON.stringify({ password }) });

function loginApi(email, password) {
    const form = new FormData();   // OAuth2 di FastAPI vuole form data con "username"
    form.append('username', email);
    form.append('password', password);
    return apiRequest('/login', { method: 'POST', body: form });
}

const requestPasswordResetApi = (email) =>
    apiRequest('/password-reset/request', { method: 'POST', body: JSON.stringify({ email }) });
const confirmPasswordResetApi = (token, newPassword) =>
    apiRequest('/password-reset/confirm', { method: 'POST', body: JSON.stringify({ token, new_password: newPassword }) });

// ====================
// RENDERING (solo createElement/textContent: nessun innerHTML con dati utente)
// ====================
function infoItem(title, text, color, iconClasses) {
    const li = document.createElement('li');
    li.className = 'todo-item';
    li.style.borderLeftColor = color;
    const content = document.createElement('div');
    content.className = 'todo-content';
    const h3 = document.createElement('h3');
    h3.append(makeIcon(iconClasses), ` ${title}`);
    const p = document.createElement('p');
    p.textContent = text;
    content.append(h3, p);
    li.append(content);
    return li;
}

function todoItem(todo) {
    const li = document.createElement('li');
    li.className = 'todo-item' + (todo.completed ? ' done' : '');
    li.dataset.id = todo.id;

    const content = document.createElement('div');
    content.className = 'todo-content';
    const h3 = document.createElement('h3');
    h3.textContent = todo.title;
    const p = document.createElement('p');
    if (todo.description) {
        p.textContent = todo.description;
    } else {
        const em = document.createElement('em');
        em.textContent = 'Nessuna descrizione';
        p.append(em);
    }
    content.append(h3, p);

    const actions = document.createElement('div');
    actions.className = 'todo-actions';
    actions.append(
        makeButton('toggle-btn', 'fas fa-check', todo.completed ? 'Riapri' : 'Fatto', () => handleToggle(todo)),
        makeButton('delete-btn', 'fas fa-trash', 'Elimina', () => handleDelete(todo.id)),
    );

    li.append(content, actions);
    return li;
}

function renderTodos(todos) {
    todosContainer.replaceChildren();
    if (todos.length === 0) {
        todosContainer.append(
            infoItem('Nessun task', 'Aggiungi il tuo primo task usando il form sopra!', '#ffa502', 'fas fa-clipboard-list'),
        );
        return;
    }
    todosContainer.append(...todos.map(todoItem));
}

async function loadTodos() {
    loadingElement.style.display = 'block';
    todosContainer.replaceChildren();
    try {
        renderTodos(await fetchTodosApi());
    } catch (error) {
        todosContainer.append(infoItem('Errore', error.message, '#ff4757', 'fas fa-exclamation-triangle'));
    } finally {
        loadingElement.style.display = 'none';
    }
}

function showAppSection() {
    authSection.style.display = 'none';
    appSection.style.display = 'block';
    $('user-email').textContent = userEmail || 'Utente';
    loadTodos();
}

function showAuthSection() {
    setSession(null, null);
    authSection.style.display = 'block';
    appSection.style.display = 'none';
}

// ====================
// HANDLER
// ====================
async function withBusyButton(button, busyHtmlIcon, busyLabel, fn) {
    const original = [...button.childNodes].map((n) => n.cloneNode(true));
    button.replaceChildren(makeIcon(busyHtmlIcon), ` ${busyLabel}`);
    button.disabled = true;
    try {
        return await fn();
    } finally {
        button.replaceChildren(...original);
        button.disabled = false;
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const email = $('login-email').value.trim();
    const password = $('login-password').value;
    await withBusyButton(loginForm.querySelector('button'), 'fas fa-spinner fa-spin', 'Accesso...', async () => {
        try {
            const data = await loginApi(email, password);
            setSession(data.access_token, email);
            $('login-password').value = '';
            showAppSection();
        } catch (error) {
            showMessage(error.message);
        }
    });
}

async function handleRegister(event) {
    event.preventDefault();
    const email = $('register-email').value.trim();
    const password = $('register-password').value;
    if (password.length < 8) {
        showMessage('La password deve essere di almeno 8 caratteri');
        return;
    }
    await withBusyButton(registerForm.querySelector('button'), 'fas fa-spinner fa-spin', 'Creazione...', async () => {
        try {
            await registerApi(email, password);
            switchTab('login');
            $('login-email').value = email;
            $('login-password').value = '';
            $('login-password').focus();
            showMessage('Account creato! Ora puoi accedere.', 'success');
        } catch (error) {
            showMessage(error.message);
        }
    });
}

async function handleTodoSubmit(event) {
    event.preventDefault();
    const title = $('title').value.trim();
    const description = $('description').value.trim();
    if (!title) {
        alert('Inserisci un titolo per il task.');
        return;
    }
    await withBusyButton(todoForm.querySelector('button'), 'fas fa-spinner fa-spin', 'Aggiungo...', async () => {
        try {
            await createTodoApi(title, description);
            $('title').value = '';
            $('description').value = '';
            await loadTodos();
        } catch (error) {
            alert(`Errore: ${error.message}`);
        }
    });
}

async function handleToggle(todo) {
    try {
        await toggleTodoApi(todo.id, !todo.completed);
        await loadTodos();
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

async function handleDelete(id) {
    if (!confirm('Sei sicuro di voler eliminare questo task?')) return;
    try {
        await deleteTodoApi(id);
        await loadTodos();
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

function handleLogout() {
    if (!confirm('Sei sicuro di voler uscire?')) return;
    showAuthSection();
    $('login-email').value = '';
    $('login-password').value = '';
    authMessage.style.display = 'none';
}

function openDeleteAccountModal() {
    $('delete-account-password').value = '';
    $('delete-account-modal').style.display = 'flex';
}

function closeDeleteAccountModal() {
    $('delete-account-modal').style.display = 'none';
}

async function handleDeleteAccountSubmit(event) {
    event.preventDefault();
    const password = $('delete-account-password').value;
    if (!confirm('Confermi la cancellazione definitiva dell\'account?')) return;

    try {
        await deleteAccountApi(password);
        closeDeleteAccountModal();
        alert('Account eliminato.');
        showAuthSection();
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

function openForgotPasswordModal() {
    $('forgot-password-email').value = '';
    $('forgot-password-modal').style.display = 'flex';
}

function closeForgotPasswordModal() {
    $('forgot-password-modal').style.display = 'none';
}

async function handleForgotPasswordSubmit(event) {
    event.preventDefault();
    const email = $('forgot-password-email').value.trim();
    try {
        const data = await requestPasswordResetApi(email);
        closeForgotPasswordModal();
        alert(data.message);  // messaggio generico dal backend, sempre lo stesso per sicurezza
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

let currentResetToken = null;

function openResetPasswordModal(token) {
    currentResetToken = token;
    $('reset-password-new').value = '';
    $('reset-password-modal').style.display = 'flex';
}

async function handleResetPasswordSubmit(event) {
    event.preventDefault();
    const newPassword = $('reset-password-new').value;
    if (newPassword.length < 8) {
        alert('La password deve essere di almeno 8 caratteri.');
        return;
    }
    try {
        await confirmPasswordResetApi(currentResetToken, newPassword);
        $('reset-password-modal').style.display = 'none';
        alert('Password aggiornata. Ora puoi accedere con la nuova password.');
        location.hash = '';  // pulisce il token dall'URL, non deve restare lì
        showAuthSection();
    } catch (error) {
        alert(`Errore: ${error.message}`);
    }
}

function checkResetTokenInUrl() {
    // Il link nell'email porta a #reset-password?token=XYZ
    const match = location.hash.match(/^#reset-password\?token=(.+)$/);
    if (match) {
        openResetPasswordModal(decodeURIComponent(match[1]));
    }
}

function switchTab(tabName) {
    tabButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.tab === tabName));
    authForms.forEach((form) => form.classList.toggle('active', form.id === `${tabName}-form`));
    authMessage.style.display = 'none';
}

// ====================
// INIT
// ====================
function init() {
    tabButtons.forEach((btn) => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    todoForm.addEventListener('submit', handleTodoSubmit);
    $('refresh-btn').addEventListener('click', loadTodos);
    $('logout-btn').addEventListener('click', handleLogout);
    $('delete-account-btn').addEventListener('click', openDeleteAccountModal);
    $('delete-account-cancel').addEventListener('click', closeDeleteAccountModal);
    $('delete-account-form').addEventListener('submit', handleDeleteAccountSubmit);
    $('forgot-password-link').addEventListener('click', (e) => { e.preventDefault(); openForgotPasswordModal(); });
    $('forgot-password-cancel').addEventListener('click', closeForgotPasswordModal);
    $('forgot-password-form').addEventListener('submit', handleForgotPasswordSubmit);
    $('reset-password-form').addEventListener('submit', handleResetPasswordSubmit);

    checkResetTokenInUrl();  // nel caso l'utente arrivi già con il link dall'email

    $('api-url').textContent = API_BASE_URL;
    const docsLink = $('docs-link');
    if (docsLink) docsLink.href = `${API_BASE_URL}/docs`;

    if (authToken) showAppSection();   // se il token è scaduto, il primo 401 riporta al login
    else showAuthSection();
}

document.addEventListener('DOMContentLoaded', init);
