import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import configparser
import threading
import time
from database import init_db, get_db, cleanup, periodic_checkpoint
import signal
import sys

# Load config.ini to get the path
config = configparser.ConfigParser()
config.read('config.ini')

# Production server setup
production = True  # Set to True for production, False for development
pool_monitoring = config.getboolean("ConnectionPool", "monitoring")  # Enable or disable pool monitoring
use_connection_pool = config.getboolean("ConnectionPool", "use_pool")  # Use connection pool; if False, use direct connections

cpu_count = os.cpu_count()
pool_size = cpu_count if cpu_count else int(config["ConnectionPool"]["pool_size"])  # Connection pool size use logical processors
if not pool_size or pool_size < 1:
    raise ValueError("Invalid pool size in config.ini, must be at least 1")

use_wal = config.getboolean("ConnectionPool", "use_wal")  # Use WAL mode for SQLite
continuous_pool_monitoring = False  # If True, monitor pool continuously (not recommended, for testing only)

if production:
    from waitress import serve
    import socket

# Initialize the Dash app
# Get URL prefix from environment variable or use default
URL_PREFIX = os.environ.get('DASH_URL_BASE_PATHNAME', '/et/')
APP_PORT = int(os.environ.get('APP_PORT', '8080'))

# In main.py, after creating the app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LUX, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    url_base_pathname=URL_PREFIX,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)

app.title = 'Gringotts - Finance Safety'
server = app.server

# Configure Flask-Login
server.config.update(
    SECRET_KEY=os.urandom(32).hex(),  # use real key in production
)

login_manager = LoginManager()
login_manager.init_app(server)
# Set login view to include the URL prefix
login_manager.login_view = f'{URL_PREFIX}login'

# User model
class User(UserMixin):
    def __init__(self, user_id, username, email=None, name=None):
        self.id = user_id
        self.username = username
        self.email = email
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user_data = db.get_user_by_id(int(user_id))
    if user_data and user_data[5]:  # is_active check
        return User(user_data[0], user_data[1], user_data[3], user_data[4])
    return None

# Define a common navbar with login/logout button
def get_navbar():
    user_info = ""
    if current_user.is_authenticated:
        user_info = f"Welcome, {current_user.name or current_user.username}"
    
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href=f"{URL_PREFIX}")),
            dbc.NavItem(dbc.NavLink("Data", href=f"{URL_PREFIX}data")),
            dbc.NavItem(dbc.NavLink(user_info, disabled=True))
            if current_user.is_authenticated
            else None,
            dbc.NavItem(
                dbc.NavLink(
                    "Login" if not current_user.is_authenticated else "Logout",
                    href=f"{URL_PREFIX}login"
                    if not current_user.is_authenticated
                    else f"{URL_PREFIX}logout",
                )
            ),
            dbc.NavItem(dbc.NavLink("Register", href=f"{URL_PREFIX}register"))
            if not current_user.is_authenticated
            else None,
        ],
        brand="Gringotts",
        brand_href=f"{URL_PREFIX}",
        brand_style={
            # "fontFamily": "'Montserrat', 'Helvetica Neue', sans-serif",
            # "fontSize": "1.7rem",
            # "fontWeight": "700",
            # "letterSpacing": "1px",
            # "color": "#ffffff",
            # "textTransform": "uppercase"
            "fontFamily": "'Playfair Display', Georgia, serif",
            "fontSize": "1.9rem",
            "fontWeight": "600",
            "letterSpacing": "0.8px",
            "color": "#ffffff",
            "textShadow": "0 1px 2px rgba(0,0,0,0.1)",
        },
        color="primary",
        dark=True,
    )

# Login page layout
login_layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1("Login", className="text-center mt-5"),
                    dbc.Input(
                        id="login-username",
                        type="text",
                        placeholder="Username",
                        className="mb-3",
                    ),
                    dbc.Input(
                        id="login-password",
                        type="password",
                        placeholder="Password",
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Login", id="login-button", color="primary", className="w-100"
                    ),
                    html.Div(
                        [
                            "Don't have an account? ",
                            dcc.Link(
                                "Register",
                                href=f"{URL_PREFIX}register",
                                className="text-primary",
                            ),
                        ],
                        className="text-center mt-3",
                    ),
                    html.Div(id="login-message", className="mt-3"),
                ],
                width=6,
            ),
            justify="center",
        )
    ],
    className="mt-5",
)

# Registration page layout
registration_layout = dbc.Container(
    [
        dbc.Row(
            dbc.Col(
                [
                    html.H1("Register", className="text-center mt-5"),
                    dbc.Input(
                        id="register-username",
                        type="text",
                        placeholder="Username",
                        className="mb-3",
                    ),
                    dbc.Input(
                        id="register-email",
                        type="email",
                        placeholder="Email (optional)",
                        className="mb-3",
                    ),
                    dbc.Input(
                        id="register-name",
                        type="text",
                        placeholder="Full Name (optional)",
                        className="mb-3",
                    ),
                    dbc.Input(
                        id="register-password",
                        type="password",
                        placeholder="Password",
                        className="mb-3",
                    ),
                    dbc.Input(
                        id="register-confirm-password",
                        type="password",
                        placeholder="Confirm Password",
                        className="mb-3",
                    ),
                    dbc.Button(
                        "Register",
                        id="register-button",
                        color="primary",
                        className="w-100",
                    ),
                    html.Div(
                        [
                            html.Span("Already have an account? "),
                            dcc.Link("Login here", href=f"{URL_PREFIX}login"),
                        ],
                        className="mt-3 text-center",
                    ),
                    html.Div(id="register-message", className="mt-3"),
                ],
                width=6,
            ),
            justify="center",
        )
    ],
    className="mt-5",
)

# Main layout includes a location component for URL routing
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="navbar-container"),
    html.Div(id="page-content")
])

# Pool Monitor class
class PoolMonitor:
    def __init__(self, db, check_interval=30, continuous = False):
        self.db = db
        self.check_interval = check_interval
        self.running = False
        self.thread = None
        self.continuous = continuous
        
    def start_monitoring(self):
        """Start background monitoring"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print("Pool monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        if self.thread:
            self.thread.join()
        print("Pool monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        alert_count = 0
        last_alert_time = 0
        
        while self.running:
            try:
                
                if self.continuous:

                    # Continuous mode: print stats every ms
                    print("\033c", end="")  # ANSI escape code to clear screen
                    self.db.print_pool_stats()
                    #time.sleep(0.001)
                
                else:
                
                    health = self.db.get_pool_health()
                    
                    # Check for issues
                    if health['status'] in ['WARNING', 'CRITICAL']:
                        current_time = time.time()
                        
                        # Rate limit alerts (max 1 per minute)
                        if current_time - last_alert_time > 60:
                            self._send_alert(health)
                            last_alert_time = current_time
                            alert_count += 1
                    
                    # Log metrics periodically (every 5 minutes)
                    if int(time.time()) % 300 == 0:
                        self._log_metrics()
                    
                    time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Error in pool monitoring: {e}")
                time.sleep(self.check_interval)
    
    def _send_alert(self, health):
        """Send alert when pool has issues"""
        print(f"🚨 POOL ALERT: {health['status']}")
        print(f"   Utilization: {health['utilization_percent']}%")
        print(f"   Active: {health['active_connections']}")
        print(f"   Failed Checkouts: {health['failed_checkouts']}")
    
    def _log_metrics(self):
        """Log current metrics"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        health = self.db.get_pool_health()
        print(f"[{timestamp}] Pool Health: {health['status']}, "
              f"Utilization: {health['utilization_percent']}%, "
              f"Active: {health['active_connections']}")

# Lazy import functions for page layouts and callbacks
def get_homepage_layout():
    """Lazy import homepage layout"""
    from homepage import homepage_layout
    return homepage_layout()

def get_datapage_layout():
    """Lazy import datapage layout"""
    from datapage import data_page_layout
    return data_page_layout()

def register_homepage_callbacks():
    """Lazy import and register homepage callbacks"""
    from homepage import home_callbacks
    home_callbacks(app)

def register_datapage_callbacks():
    """Lazy import and register datapage callbacks"""
    from datapage import data_page_callbacks
    data_page_callbacks(app)

# Routing callback to switch between pages based on the URL path
@app.callback(
    [Output("page-content", "children"),
     Output("navbar-container", "children")],
    [Input("url", "pathname")],
    [State("url", "search")]
)
def display_page(pathname, search):
    # Strip the URL prefix to get the actual route
    if pathname and pathname.startswith(URL_PREFIX):
        route = pathname[len(URL_PREFIX):].lstrip('/')
    else:
        route = ''
    
    if route == 'login':
        if current_user.is_authenticated:
            return dash.no_update, dash.no_update
        return login_layout, get_navbar()
    elif route == 'logout':
        if current_user.is_authenticated:
            logout_user()
        return dcc.Location(pathname=f"{URL_PREFIX}", id="logout-redirect"), get_navbar()
    elif route == 'data':
        if not current_user.is_authenticated:
           return dcc.Location(pathname=f"{URL_PREFIX}login", id="data-login-redirect"), get_navbar()
        return get_datapage_layout(), get_navbar()
    elif route == 'register':
        if current_user.is_authenticated:
            return dcc.Location(pathname=f"{URL_PREFIX}", id="register-redirect"), get_navbar()
        return registration_layout, get_navbar()
    else:
        if not current_user.is_authenticated:
           return dcc.Location(pathname=f"{URL_PREFIX}login", id="home-login-redirect"), get_navbar()
        return get_homepage_layout(), get_navbar()

# Login callback
@app.callback(
    Output("login-message", "children"),
    [Input("login-button", "n_clicks")],
    [State("login-username", "value"),
     State("login-password", "value")]
)
def login_user_callback(n_clicks, username, password):
    if n_clicks is None:
        return ""

    db = get_db()
    user_data = db.get_user_by_username(username)

    if (
        user_data and check_password_hash(user_data[2], password) and user_data[5]
    ):  # is_active check
        user = User(user_data[0], user_data[1], user_data[3], user_data[4])
        login_user(user)
        return dcc.Location(pathname=f"{URL_PREFIX}", id="login-success-redirect")
    else:
        return dbc.Alert("Invalid username or password", color="danger")

# Registration callback
@app.callback(
    Output("register-message", "children"),
    [Input("register-button", "n_clicks")],
    [
        State("register-username", "value"),
        State("register-email", "value"),
        State("register-name", "value"),
        State("register-password", "value"),
        State("register-confirm-password", "value"),
    ],
)
def register_user(n_clicks, username, email, name, password, confirm_password):
    if n_clicks is None:
        return ""

    # Validation
    if not username or not password:
        return dbc.Alert("Username and password are required", color="danger")

    if password != confirm_password:
        return dbc.Alert("Passwords do not match", color="danger")

    if len(password) < 8:
        return dbc.Alert("Password must be at least 8 characters long", color="danger")

    # Create user
    db = get_db()
    password_hash = generate_password_hash(password)
    user_id = db.create_user(username, password_hash, email, name)

    if user_id:
        return dbc.Alert("Registration successful! You can now login.", color="success")
    else:
        return dbc.Alert("Username or email already exists", color="danger")

# --- Handle termination signals for graceful shutdown ---
def handle_sigterm(signum, frame):
    """Handle SIGTERM signal for graceful shutdown."""
    print("Received SIGTERM, initiating graceful shutdown...")
    if 'monitor' in globals():
        monitor.stop_monitoring()
    cleanup()
    sys.exit(0)

# INITIALIZE
if __name__ == "__main__":

    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)  # Also handle CTRL+C

    try: 
        # --- LAUNCH BACKEND FIRST ---
        print("Initializing database...")
        init_db(use_pool_init=use_connection_pool, pool_size_init=pool_size, enable_monitoring_init=pool_monitoring, use_wal_init=use_wal)
        db = get_db()
        
        # Initialize pool monitoring (separate)
        if use_connection_pool and pool_monitoring:
            print("Setting up pool monitoring...")
            monitor = PoolMonitor(db, check_interval=30, continuous = continuous_pool_monitoring)

            # Start monitoring
            monitor.start_monitoring()
        
        # In Docker with WAL pool mode, start periodic checkpoints
        if use_wal:
            if db.use_wal:
                print("Starting periodic WAL checkpoints for Docker...")
                periodic_checkpoint(db, interval_seconds=300)  # Checkpoint every 5 min

        print("Registering page callbacks...")
        # Register callbacks (post database initialization)
        register_homepage_callbacks()
        register_datapage_callbacks()
        
        print("Starting web server...")
        if not production:
            # Run the app in debug mode for development
            app.run_server(debug=True)
        else:
            # Get local IP (for LAN access)
            local_ip = socket.gethostbyname(socket.gethostname())

            #host = local_ip  # Restrict to local IP for LAN access
            host = '0.0.0.0'
            port = APP_PORT
            
            print("╔════════════════════════════════╗")
            print("║   Waitress Server Started      ║")
            print("╠════════════════════════════════╣")
            print(f"║ Local:  http://localhost:{port}{URL_PREFIX} ║")
            print(f"║ LAN:    http://{local_ip}:{port}{URL_PREFIX}  ║")
            print("╚════════════════════════════════╝")
            
            serve(app.server, host=host, port=port)

    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    except Exception as e:
        print(f"Error during initialization: {e}")
        raise
    finally:
        print("\nShutting down application...")
        
        # Stop monitor if exists
        if 'monitor' in locals():
            monitor.stop_monitoring()
        
        # Explicit cleanup with checkpoint
        cleanup()
        
        print("Application shutdown complete")
