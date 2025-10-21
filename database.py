# database.py
import sqlite3
from queue import Queue, Empty
from contextlib import contextmanager
import pandas as pd
import configparser
import os

# Pool monitoring imports
import threading
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import json

@dataclass
class ConnectionStats:
    """Statistics for a single connection"""
    connection_id: str
    created_at: datetime
    last_used: datetime
    total_uses: int
    current_status: str  # 'available', 'in_use'
    total_time_in_use: float  # seconds

@dataclass
class PoolMetrics:
    """Overall pool metrics"""
    total_connections: int
    active_connections: int
    available_connections: int
    peak_active_connections: int
    total_checkouts: int
    total_checkins: int
    average_checkout_time: float
    current_wait_queue_size: int
    failed_checkouts: int
    pool_created_at: datetime

# Initialize SQLite connection pool class
class SQLiteConnectionPool:
    def __init__(self, db_path, pool_size=8, enable_monitoring=True, use_wal = True):
                self.db_path = db_path
                self.pool_size = pool_size
                self.pool = Queue(maxsize=pool_size)
                self.use_wal = use_wal
                self.enable_monitoring = enable_monitoring
                
                # Monitoring attributes
                self._lock = threading.RLock()
                self._connection_stats: Dict[str, ConnectionStats] = {}
                self._active_connections: Dict[str, datetime] = {}  # connection_id -> checkout_time
                self._checkout_times: List[float] = []  # Track checkout durations
                self._total_checkouts = 0
                self._total_checkins = 0
                self._peak_active = 0
                self._failed_checkouts = 0
                self._pool_created_at = datetime.now()
                self._waiting_threads = 0

                # Map connection objects to their IDs
                self._connection_id_map: Dict[int, str] = {}
                
                # Initialize connections
                for i in range(pool_size):
                    conn = self._create_connection()
                    conn_id = f"conn_{i}_{id(conn)}"
                    self._connection_id_map[id(conn)] = conn_id  # Use object id as key
                    self.pool.put(conn)
                    
                    if self.enable_monitoring:
                        self._connection_stats[conn_id] = ConnectionStats(
                            connection_id=conn_id,
                            created_at=datetime.now(),
                            last_used=datetime.now(),
                            total_uses=0,
                            current_status='available',
                            total_time_in_use=0.0
                        )

    def _create_connection(self):
        """Create a connection with Docker-friendly settings"""
        conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,  # Allow multi-threaded access
            timeout=30.0
        )
        
        # Docker-friendly settings
        if self.use_wal:
            # Use WAL but with proper checkpoint settings
            conn.execute('PRAGMA journal_mode=WAL')
            # More aggressive auto-checkpoint (default is 1000)
            conn.execute('PRAGMA wal_autocheckpoint=500')
        else:
            # Alternative: Use DELETE mode which is more Docker-friendly
            conn.execute('PRAGMA journal_mode=DELETE')
        
        # Use FULL synchronous for data safety in Docker
        conn.execute('PRAGMA synchronous=FULL')
        
        # Reduce cache size to force more frequent disk writes
        conn.execute('PRAGMA cache_size=-2000')  # 2MB cache
        
        # Enable foreign keys
        conn.execute('PRAGMA foreign_keys=ON')
        
        return conn
    
    def checkpoint_wal(self):
        """Manually checkpoint WAL file to main database"""
        if not self.use_wal:
            return
            
        try:
            # Get a connection from the pool temporarily
            conn = self.pool.get(timeout=5.0)
            try:
                # RESTART mode ensures complete checkpoint
                result = conn.execute('PRAGMA wal_checkpoint(RESTART)').fetchone()
                if result:
                    print(f"WAL Checkpoint complete: {result}")
                conn.commit()
            finally:
                self.pool.put(conn)
        except Exception as e:
            print(f"Error during WAL checkpoint: {e}")

    @contextmanager
    def get_connection(self, timeout=10.0):
        checkout_start = time.time()
        conn = None
        
        try:
            if self.enable_monitoring:
                with self._lock:
                    self._waiting_threads += 1
            
            # Try to get connection with timeout
            try:
                conn = self.pool.get(timeout=timeout)
            except Empty:
                if self.enable_monitoring:
                    with self._lock:
                        self._failed_checkouts += 1
                raise TimeoutError(f"Could not get connection within {timeout} seconds")
            
            checkout_time = time.time() - checkout_start
            
            if self.enable_monitoring:
                self._update_checkout_stats(conn, checkout_time)
            
            yield conn
            
        finally:
            if conn:
                if self.enable_monitoring:
                    self._update_checkin_stats(conn)
                self.pool.put(conn)
            
            if self.enable_monitoring:
                with self._lock:
                    self._waiting_threads = max(0, self._waiting_threads - 1)

    def _get_connection_id(self, conn):
        """Get connection ID from the connection object"""
        return self._connection_id_map.get(id(conn), 'unknown')

    def _update_checkout_stats(self, conn, checkout_time):
        """Update statistics when connection is checked out"""
        with self._lock:
            conn_id = self._get_connection_id(conn)
            now = datetime.now()
            
            self._total_checkouts += 1
            self._checkout_times.append(checkout_time)
            
            # Keep only last 1000 checkout times for memory efficiency
            if len(self._checkout_times) > 1000:
                self._checkout_times = self._checkout_times[-1000:]
            
            self._active_connections[conn_id] = now
            current_active = len(self._active_connections)
            self._peak_active = max(self._peak_active, current_active)
            
            if conn_id in self._connection_stats:
                stats = self._connection_stats[conn_id]
                stats.current_status = 'in_use'
                stats.last_used = now
                stats.total_uses += 1

    def _update_checkin_stats(self, conn):
        """Update statistics when connection is returned to pool"""
        with self._lock:
            conn_id = self._get_connection_id(conn)
            
            self._total_checkins += 1
            
            if conn_id in self._active_connections:
                checkout_time = self._active_connections.pop(conn_id)
                time_in_use = (datetime.now() - checkout_time).total_seconds()
                
                if conn_id in self._connection_stats:
                    stats = self._connection_stats[conn_id]
                    stats.current_status = 'available'
                    stats.total_time_in_use += time_in_use

    def get_pool_metrics(self) -> PoolMetrics:
        """Get current pool metrics"""
        with self._lock:
            avg_checkout_time = (
                sum(self._checkout_times) / len(self._checkout_times) 
                if self._checkout_times else 0.0
            )
            
            return PoolMetrics(
                total_connections=self.pool_size,
                active_connections=len(self._active_connections),
                available_connections=self.pool.qsize(),
                peak_active_connections=self._peak_active,
                total_checkouts=self._total_checkouts,
                total_checkins=self._total_checkins,
                average_checkout_time=avg_checkout_time,
                current_wait_queue_size=self._waiting_threads,
                failed_checkouts=self._failed_checkouts,
                pool_created_at=self._pool_created_at
            )

    def get_connection_stats(self) -> List[ConnectionStats]:
        """Get statistics for all connections"""
        with self._lock:
            return list(self._connection_stats.values())

    def get_pool_health(self) -> Dict:
        """Get pool health summary"""
        metrics = self.get_pool_metrics()
        uptime = datetime.now() - metrics.pool_created_at
        
        # Calculate utilization percentage
        utilization = (metrics.active_connections / metrics.total_connections) * 100
        
        # Determine health status
        if utilization > 90:
            health_status = "CRITICAL"
        elif utilization > 75:
            health_status = "WARNING"
        elif metrics.failed_checkouts > 0:
            health_status = "DEGRADED"
        else:
            health_status = "HEALTHY"
        
        return {
            "status": health_status,
            "utilization_percent": round(utilization, 2),
            "uptime_seconds": uptime.total_seconds(),
            "active_connections": metrics.active_connections,
            "available_connections": metrics.available_connections,
            "failed_checkouts": metrics.failed_checkouts,
            "avg_checkout_time_ms": round(metrics.average_checkout_time * 1000, 2),
            "waiting_threads": metrics.current_wait_queue_size
        }

    def print_stats(self):
        """Print formatted pool statistics"""
        metrics = self.get_pool_metrics()
        health = self.get_pool_health()
        
        print("\n" + "="*50)
        print("SQLite Connection Pool Statistics")
        print("="*50)
        print(f"Pool Health: {health['status']}")
        print(f"Total Connections: {metrics.total_connections}")
        print(f"Active Connections: {metrics.active_connections}")
        print(f"Available Connections: {metrics.available_connections}")
        print(f"Utilization: {health['utilization_percent']}%")
        print(f"Peak Active: {metrics.peak_active_connections}")
        print(f"Total Checkouts: {metrics.total_checkouts}")
        print(f"Total Checkins: {metrics.total_checkins}")
        print(f"Failed Checkouts: {metrics.failed_checkouts}")
        print(f"Average Checkout Time: {health['avg_checkout_time_ms']} ms")
        print(f"Current Wait Queue: {metrics.current_wait_queue_size}")
        print(f"Pool Uptime: {health['uptime_seconds']:.1f} seconds")
        
        # Connection details
        conn_stats = self.get_connection_stats()
        print(f"\nConnection Details:")
        for stat in conn_stats:
            print(f"  {stat.connection_id}: {stat.current_status}, "
                  f"uses: {stat.total_uses}, "
                  f"total_time: {stat.total_time_in_use:.2f}s")
        print("="*50)

    def export_metrics_json(self, filepath: Optional[str] = None) -> str:
        """Export metrics to JSON format"""
        metrics = self.get_pool_metrics()
        health = self.get_pool_health()
        conn_stats = self.get_connection_stats()
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "pool_metrics": {
                "total_connections": metrics.total_connections,
                "active_connections": metrics.active_connections,
                "available_connections": metrics.available_connections,
                "peak_active_connections": metrics.peak_active_connections,
                "total_checkouts": metrics.total_checkouts,
                "total_checkins": metrics.total_checkins,
                "average_checkout_time": metrics.average_checkout_time,
                "current_wait_queue_size": metrics.current_wait_queue_size,
                "failed_checkouts": metrics.failed_checkouts,
                "pool_created_at": metrics.pool_created_at.isoformat()
            },
            "health": health,
            "connections": [
                {
                    "connection_id": stat.connection_id,
                    "created_at": stat.created_at.isoformat(),
                    "last_used": stat.last_used.isoformat(),
                    "total_uses": stat.total_uses,
                    "current_status": stat.current_status,
                    "total_time_in_use": stat.total_time_in_use
                }
                for stat in conn_stats
            ]
        }
        
        json_str = json.dumps(data, indent=2)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            print(f"Metrics exported to {filepath}")
        
        return json_str

    def reset_stats(self):
        """Reset all statistics (useful for testing)"""
        with self._lock:
            self._checkout_times.clear()
            self._total_checkouts = 0
            self._total_checkins = 0
            self._peak_active = 0
            self._failed_checkouts = 0
            self._pool_created_at = datetime.now()
            
            # Reset connection stats but keep structure
            for conn_id, stats in self._connection_stats.items():
                stats.total_uses = 0
                stats.total_time_in_use = 0.0
                stats.last_used = datetime.now()

    def close_all(self):
        """Close all connections with proper cleanup"""
        if self.enable_monitoring:
            print("\nFinal Pool Statistics:")
            self.print_stats()
        
        # First, checkpoint WAL if enabled
        if self.use_wal:
            print("Performing final WAL checkpoint...")
            self.checkpoint_wal()
            time.sleep(0.5)  # Give it time to complete
        
        # Then close all connections
        closed_count = 0
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                # Ensure any pending transactions are committed
                try:
                    conn.commit()
                except:
                    pass
                conn.close()
                closed_count += 1
            except Empty:
                break
        
        print(f"Closed {closed_count} connections")
        
        # For Docker: ensure file handles are released
        if hasattr(os, 'sync'):
            os.sync()  # Force filesystem sync on Unix-like systems

# --- Database class ---
class ExpenseDB:
    
    def __init__(self, db_path, use_pool = True, pool_size=8, enable_monitoring=True, use_wal=True):
        """
        Initialize ExpenseDB with Docker-friendly options
        
        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections in pool
            enable_monitoring: Enable pool statistics
            use_wal: Use WAL mode (set False for better Docker compatibility)
            use_pool: Use connection pooling (default True)
        """
        self.db_path = db_path
        self.use_pool = use_pool
        self.use_wal = use_wal

        if use_pool:
            self.pool = SQLiteConnectionPool(
                db_path, 
                pool_size, 
                enable_monitoring,
                use_wal=use_wal
            )
            self._direct_conn = None
        else:
            self.pool = None
            # Create a single direct connection
            self._direct_conn = self._create_direct_connection(use_wal)

    # --- User Management Methods ---
    def create_user(self, username, password_hash, email=None, name=None):
        """Create a new user"""
        with self._get_cursor() as cursor:
            try:
                cursor.execute(
                    """INSERT INTO users (username, password_hash, email, name) 
                    VALUES (?, ?, ?, ?)""",
                    (username, password_hash, email, name),
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None  # Username or email already exists

    def get_user_by_username(self, username):
        """Get user by username"""
        with self._get_cursor() as cursor:
            cursor.execute(
                """SELECT id, username, password_hash, email, name, is_active 
                FROM users WHERE username = ?""",
                (username,),
            )
            return cursor.fetchone()

    def get_user_by_id(self, user_id):
        """Get user by ID"""

        with self._get_cursor() as cursor:
            cursor.execute(
                """SELECT id, username, password_hash, email, name, is_active 
                FROM users WHERE id = ?""",
                (user_id,),
            )
            return cursor.fetchone()


    def update_user(self, user_id, **kwargs):
        """Update user information"""
        allowed_fields = ["email", "name", "password_hash"]
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]

        with self._get_cursor() as cursor:
            cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
            return cursor.rowcount > 0
    # ---------------------------------------------------------

    # --- Checkpoint Methods ---
    def perform_checkpoint(self):
        """Manually trigger WAL checkpoint"""
        if self.use_pool:
            self.pool.checkpoint_wal()
        else:
            try:
                result = self._direct_conn.execute('PRAGMA wal_checkpoint(RESTART)').fetchone()
                if result:
                    print(f"WAL Checkpoint complete: {result}")
                self._direct_conn.commit()
            except Exception as e:
                print(f"Error during WAL checkpoint: {e}")

    @contextmanager
    def _get_cursor(self):
        if self.use_pool:
            # Use connection pool
            with self.pool.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    yield cursor
                    conn.commit()
                except:
                    conn.rollback()
                    raise
        else:
            # Use direct connection
            cursor = self._direct_conn.cursor()
            try:
                yield cursor
                self._direct_conn.commit()
            except:
                self._direct_conn.rollback()
                raise

    def _create_direct_connection(self, use_wal=True):
        """Create a single direct connection (non-pooled)"""
        conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            timeout=30.0
        )
        
        # Apply same settings as pooled connections
        if use_wal:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA wal_autocheckpoint=500')
        else:
            conn.execute('PRAGMA journal_mode=DELETE')
        
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('PRAGMA cache_size=-2000')
        conn.execute('PRAGMA foreign_keys=ON')
        
        return conn

    def get_pool_stats(self):
        """Convenience method to access pool statistics"""
        if self.use_pool:
            return self.pool.get_pool_metrics()
        else:
            return None
    
    def get_pool_health(self):
        """Convenience method to access pool health"""
        if self.use_pool:
            return self.pool.get_pool_health()
        else:
            return {"status": "DIRECT_MODE", "note": "Not using connection pool"}
    
    def print_pool_stats(self):
        """Convenience method to print pool statistics"""
        if self.use_pool:
            self.pool.print_stats()
        else:
            print("Direct connection mode - no pool statistics available")
    
    def export_pool_metrics(self, filepath=None):
        """Convenience method to export pool metrics"""
        if self.use_pool:
            return self.pool.export_metrics_json(filepath)
        else:
            return '{"mode": "direct", "note": "No pool metrics in direct mode"}'

    # --- Main Database Methods ---
    
    # --------------- Tags ----------------------------------
    #Tags table and indexes creation method, use if missing
    def create_tags_table(self):
        
        with self._get_cursor() as cursor:
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                        tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        transaction_id INTEGER NOT NULL,
                        tag_name TEXT NOT NULL,
                        tag_color TEXT NOT NULL,
                        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER,
                        FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)

            # index by transaction_id
            cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tags_transaction_id 
                    ON tags(transaction_id)
                """)
            
            # index by user_id
            cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tags_user_id 
                    ON tags(user_id)
                """)

    def add_tag_to_transaction(self, transaction_id, tag_name, tag_color, user_id=None):

        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO tags (transaction_id, tag_name, tag_color, user_id)
                VALUES (?, ?, ?, ?)
            """, (transaction_id, tag_name, tag_color, user_id))

    def fetch_unique_tags(self, user_id=None):

        with self._get_cursor() as cursor:
            query = """
                SELECT DISTINCT tag_name, tag_color, COUNT(*) as usage_count
                FROM tags
                WHERE 1=1
            """
            params = []

            if user_id is not None:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " GROUP BY tag_name, tag_color ORDER BY tag_name"

            cursor.execute(query, params)
            tags = cursor.fetchall()

        return tags

    def get_tags_for_transaction(self, transaction_id, user_id=None):

        with self._get_cursor() as cursor:
            if user_id is not None:
                cursor.execute("""
                    SELECT tag_id, tag_name, tag_color, date_created
                    FROM tags
                    WHERE transaction_id = ? AND user_id = ?
                    ORDER BY date_created DESC
                """, (transaction_id, user_id))
            else:
                cursor.execute("""
                    SELECT tag_id, tag_name, tag_color, date_created
                    FROM tags
                    WHERE transaction_id = ?
                    ORDER BY date_created DESC
                """, (transaction_id,))
            return cursor.fetchall()

    def remove_tag(self, tag_id, user_id=None):

        with self._get_cursor() as cursor:
            if user_id is not None:
                cursor.execute("DELETE FROM tags WHERE tag_id = ? AND user_id = ?", (tag_id, user_id))
            else:
                cursor.execute("DELETE FROM tags WHERE tag_id = ?", (tag_id,))

    def get_transactions_by_tag(self, tag_name, user_id=None):

        with self._get_cursor() as cursor:
            query = """
                SELECT DISTINCT t.*
                FROM transactions t
                JOIN tags tg ON t.id = tg.transaction_id
                WHERE tg.tag_name = ?
            """
            params = [tag_name]
            
            if user_id is not None:
                query += " AND tg.user_id = ?"
                params.append(user_id)
            
            cursor.execute(query, params)
            return cursor.fetchall()  

    # ------------------------------------------------------
    def get_total_spent_by_category_filtered(
        self, start_date=None, end_date=None, user_id=None
    ):
        with self._get_cursor() as cursor:
            # Query for regular transactions
            regular_query = """
                SELECT c.name, SUM(t.amount)
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """
            params = []

            if user_id:
                regular_query += " AND t.user_id = ? AND c.user_id = ?"
                params.extend([user_id, user_id])

            if start_date and end_date:
                regular_query += " AND date(t.date) BETWEEN date(?) AND date(?)"
                params.extend([start_date, end_date])
            regular_query += " GROUP BY c.name"

            # Query for monthly recurring transactions and generate occurrences
            recurring_query = """
                WITH RECURSIVE occurrences AS (
                    SELECT 
                        rt.trans_id,
                        rt.category_id,
                        rt.amount,
                        rt.date as original_date,
                        date(rt.date, '+1 month') as occurrence_date,  -- Start from next month
                        1 as iteration
                    FROM recurringTransactions rt
                    WHERE rt.recurring = 1
            """

            if user_id:
                recurring_query += " AND rt.user_id = ?"

            recurring_query += """
                    UNION ALL
                    
                    SELECT 
                        o.trans_id,
                        o.category_id,
                        o.amount,
                        o.original_date,
                        date(o.original_date, '+' || (iteration+1) || ' month') as occurrence_date,
                        iteration+1
                    FROM occurrences o
                    WHERE date(o.original_date, '+' || (iteration+1) || ' month') <= date(?)
                )
                SELECT c.name, SUM(o.amount)
                FROM occurrences o
                JOIN categories c ON o.category_id = c.id
                WHERE 1=1
            """

            if user_id:
                recurring_query += " AND c.user_id = ?"

            recurring_query += (
                " AND date(o.occurrence_date) BETWEEN date(?) AND date(?) GROUP BY c.name"
            )

            if start_date and end_date:
                # Execute both queries and combine results
                cursor.execute(regular_query, params)
                regular_results = cursor.fetchall()

                recurring_params = []
                if user_id:
                    recurring_params.append(user_id)
                recurring_params.extend([end_date])
                if user_id:
                    recurring_params.append(user_id)
                recurring_params.extend([start_date, end_date])

                cursor.execute(recurring_query, recurring_params)
                recurring_results = cursor.fetchall()

                # Combine results
                combined = {}
                for name, amount in regular_results + recurring_results:
                    combined[name] = combined.get(name, 0) + amount

                return list(combined.items())
            else:
                # No date range - just use regular transactions
                cursor.execute(regular_query, params)
                return cursor.fetchall()


    def get_transactions_for_category(
        self, category_name, start_date=None, end_date=None, user_id=None
    ):
        with self._get_cursor() as cursor:
            # Base query for regular transactions
            regular_query = """
                SELECT t.merchant, t.amount
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE c.name = ?
            """
            params = [category_name]

            if user_id:
                regular_query += " AND t.user_id = ? AND c.user_id = ?"
                params.extend([user_id, user_id])

            if start_date and end_date:
                # Add date filter for regular transactions
                regular_query += " AND date(t.date) BETWEEN date(?) AND date(?)"
                params.extend([start_date, end_date])

                # Query for recurring transactions with generated occurrences
                recurring_query = """
                    WITH RECURSIVE occurrences AS (
                        SELECT 
                            rt.trans_id,
                            rt.merchant,
                            rt.amount,
                            rt.date as original_date,
                            date(rt.date, '+1 month') as occurrence_date,  -- Start from next month
                            1 as iteration
                        FROM recurringTransactions rt
                        JOIN categories c ON rt.category_id = c.id
                        WHERE rt.recurring = 1 AND c.name = ?
                """

                recurring_params = [category_name]
                if user_id:
                    recurring_query += " AND rt.user_id = ? AND c.user_id = ?"
                    recurring_params.extend([user_id, user_id])

                recurring_query += """
                        UNION ALL
                        
                        SELECT 
                            o.trans_id,
                            o.merchant,
                            o.amount,
                            o.original_date,
                            date(o.original_date, '+' || (iteration+1) || ' month') as occurrence_date,
                            iteration+1
                        FROM occurrences o
                        WHERE date(o.original_date, '+' || (iteration+1) || ' month') <= date(?)
                    )
                    SELECT merchant, amount
                    FROM occurrences
                    WHERE date(occurrence_date) BETWEEN date(?) AND date(?)
                """

                # Execute both queries
                cursor.execute(regular_query, params)
                regular_results = cursor.fetchall()

                recurring_params.extend([end_date, start_date, end_date])
                cursor.execute(recurring_query, recurring_params)
                recurring_results = cursor.fetchall()

                # Combine and return all results
                return regular_results + recurring_results

            else:
                # No date range - just return regular transactions
                cursor.execute(regular_query, params)
                return cursor.fetchall()


    def get_budget_by_category(self, user_id=None):
        with self._get_cursor() as cursor:
            query = """
                SELECT name, budget 
                FROM categories
                WHERE budget IS NOT NULL
            """
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            cursor.execute(query, params)
            return cursor.fetchall()


    def get_categories(self, user_id=None):
        with self._get_cursor() as cursor:
            query = """
                SELECT id, name
                FROM categories
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            cursor.execute(query, params)
            return cursor.fetchall()


    def get_monthly_spending_by_category(self, year, end_month=None, user_id=None):
        with self._get_cursor() as cursor:
            # Regular transactions query
            regular_query = """
                SELECT 
                    c.name as category,
                    strftime('%m', t.date) as month,
                    SUM(t.amount) as total
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE strftime('%Y', t.date) = ?
            """
            params = [str(year)]

            if user_id:
                regular_query += " AND t.user_id = ? AND c.user_id = ?"
                params.extend([user_id, user_id])

            if end_month:
                regular_query += " AND CAST(strftime('%m', t.date) AS INTEGER) <= ?"
                params.append(end_month)

            regular_query += """
                GROUP BY c.name, strftime('%m', t.date)
            """

            # Recurring transactions query
            recurring_query = """
                WITH RECURSIVE occurrences AS (
                    SELECT 
                        rt.trans_id,
                        rt.category_id,
                        rt.amount,
                        rt.date as original_date,
                        date(rt.date, '+1 month') as occurrence_date,
                        1 as iteration
                    FROM recurringTransactions rt
                    WHERE rt.recurring = 1
            """

            recurring_params = []
            if user_id:
                recurring_query += " AND rt.user_id = ?"
                recurring_params.append(user_id)

            recurring_query += """
                    UNION ALL

                    SELECT 
                        o.trans_id,
                        o.category_id,
                        o.amount,
                        o.original_date,
                        date(o.original_date, '+' || (iteration + 1) || ' month'),
                        iteration + 1
                    FROM occurrences o
                    WHERE strftime('%Y', date(o.original_date, '+' || (iteration + 1) || ' month')) = ?
                    AND CAST(strftime('%m', date(o.original_date, '+' || (iteration + 1) || ' month')) AS INTEGER) <= ?
                )
                SELECT 
                    c.name as category,
                    strftime('%m', o.occurrence_date) as month,
                    SUM(o.amount) as total
                FROM occurrences o
                JOIN categories c ON o.category_id = c.id
                WHERE strftime('%Y', o.occurrence_date) = ?
                AND CAST(strftime('%m', o.occurrence_date) AS INTEGER) <= ?
            """

            if user_id:
                recurring_query += " AND c.user_id = ?"

            recurring_query += " GROUP BY c.name, strftime('%m', o.occurrence_date)"

            # Execute queries
            cursor.execute(regular_query, params)
            regular_results = cursor.fetchall()

            end_month = end_month if end_month else 12
            recurring_params.extend([str(year), end_month, str(year), end_month])
            if user_id:
                recurring_params.append(user_id)

            cursor.execute(recurring_query, recurring_params)
            recurring_results = cursor.fetchall()

            # Combine the results
            combined = {}
            for category, month, total in regular_results + recurring_results:
                key = (category, month)
                combined[key] = combined.get(key, 0) + total

            # Format final output
            final = [(cat, mon, combined[(cat, mon)]) for (cat, mon) in sorted(combined)]
            return final


    def get_total_income(self, start_date=None, end_date=None, user_id=None):
        with self._get_cursor() as cursor:
            query = """
                SELECT SUM(amount) as total_income
                FROM income
                WHERE 1=1
            """
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if start_date and end_date:
                query += " AND date(date) BETWEEN date(?) AND date(?)"
                params.extend([start_date, end_date])

            cursor.execute(query, params)
            result = cursor.fetchone()

            return result[0] if result and result[0] is not None else 0.0


    def get_monthly_income_till_date(self, year, end_month=None, user_id=None):
        with self._get_cursor() as cursor:
            query = """
                SELECT 
                    strftime('%m', i.date) as month,
                    SUM(i.amount) as total
                FROM income i
                WHERE strftime('%Y', i.date) = ?
            """
            params = [str(year)]

            if user_id:
                query += " AND i.user_id = ?"
                params.append(user_id)

            if end_month:
                query += " AND strftime('%m', i.date) <= ?"
                params.append(f"{end_month:02d}")

            query += " GROUP BY month HAVING total IS NOT NULL"

            cursor.execute(query, params)
            return cursor.fetchall()


    def get_movement_trend(self, start_date, end_date, user_id=None):
        with self._get_cursor() as cursor:
            # Generate a date series from start_date to end_date
            date_series_query = """
            WITH RECURSIVE date_series(date) AS (
                SELECT date(?)
                UNION ALL
                SELECT date(date, '+1 day')
                FROM date_series
                WHERE date < date(?)
            )
            SELECT date FROM date_series
            """
            cursor.execute(date_series_query, [start_date, end_date])
            all_dates = [row[0] for row in cursor.fetchall()]

            # Get regular expenses by day
            regular_expenses_query = """
            SELECT 
                date(t.date) as day,
                SUM(t.amount) as total_spent
            FROM transactions t
            WHERE date(t.date) BETWEEN date(?) AND date(?)
            """
            params = [start_date, end_date]

            if user_id:
                regular_expenses_query += " AND t.user_id = ?"
                params.append(user_id)

            regular_expenses_query += " GROUP BY day"

            cursor.execute(regular_expenses_query, params)
            regular_expenses = {row[0]: row[1] for row in cursor.fetchall()}

            # Get recurring expenses that occur between start_date and end_date
            recurring_expenses_query = """
            WITH RECURSIVE occurrences AS (
                SELECT 
                    rt.trans_id,
                    rt.category_id,
                    rt.amount,
                    rt.date as original_date,
                    date(rt.date, '+1 month') as occurrence_date,
                    1 as iteration
                FROM recurringTransactions rt
                WHERE rt.recurring = 1
            """

            recurring_params = []
            if user_id:
                recurring_expenses_query += " AND rt.user_id = ?"
                recurring_params.append(user_id)

            recurring_expenses_query += """
                UNION ALL

                SELECT 
                    o.trans_id,
                    o.category_id,
                    o.amount,
                    o.original_date,
                    date(o.original_date, '+' || (iteration + 1) || ' month'),
                    iteration + 1
                FROM occurrences o
                WHERE date(o.original_date, '+' || (iteration + 1) || ' month') <= date(?)
            )
            SELECT 
                date(o.occurrence_date) as day,
                SUM(o.amount) as total_spent
            FROM occurrences o
            WHERE date(o.occurrence_date) BETWEEN date(?) AND date(?)
            GROUP BY day
            """

            recurring_params.extend([end_date, start_date, end_date])
            cursor.execute(recurring_expenses_query, recurring_params)
            recurring_expenses = {row[0]: row[1] for row in cursor.fetchall()}

            # Get income by day
            income_query = """
            SELECT 
                date(i.date) as day,
                SUM(i.amount) as total_income
            FROM income i
            WHERE date(i.date) BETWEEN date(?) AND date(?)
            """
            income_params = [start_date, end_date]

            if user_id:
                income_query += " AND i.user_id = ?"
                income_params.append(user_id)

            income_query += " GROUP BY day"

            cursor.execute(income_query, income_params)
            income = {row[0]: row[1] for row in cursor.fetchall()}

            # Combine all data
            result = []
            for day in all_dates:
                total_spent = regular_expenses.get(day, 0) + recurring_expenses.get(day, 0)
                total_income = income.get(day, 0)
                result.append(
                    {"date": day, "total_spent": total_spent, "total_income": total_income}
                )

            return result

    def get_all_transactions_flow(self, start_date=None, end_date=None, user_id=None):
        with self._get_cursor() as cursor:
            # --- Income query ---
            income_query = """
                SELECT source, SUM(amount)
                FROM income
                WHERE 1=1
            """
            income_params = []

            if user_id:
                income_query += " AND user_id = ?"
                income_params.append(user_id)

            if start_date and end_date:
                income_query += " AND date(date) BETWEEN date(?) AND date(?)"
                income_params.extend([start_date, end_date])
            income_query += " GROUP BY source"
            cursor.execute(income_query, income_params)
            income_data = cursor.fetchall()

            # --- Regular spending by category ---
            spending_query = """
                SELECT c.name, SUM(t.amount)
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """
            spending_params = []

            if user_id:
                spending_query += " AND t.user_id = ? AND c.user_id = ?"
                spending_params.extend([user_id, user_id])

            if start_date and end_date:
                spending_query += " AND date(t.date) BETWEEN date(?) AND date(?)"
                spending_params.extend([start_date, end_date])
            spending_query += " GROUP BY c.name"

            cursor.execute(spending_query, spending_params)
            regular_spending = cursor.fetchall()

            # --- Recurring spending by category ---
            recurring_spending_query = """
                WITH RECURSIVE occurrences AS (
                    SELECT 
                        rt.category_id,
                        rt.amount,
                        rt.date as original_date,
                        date(rt.date, '+1 month') as occurrence_date,
                        1 as iteration
                    FROM recurringTransactions rt
                    WHERE rt.recurring = 1
            """

            recurring_spending_params = []
            if user_id:
                recurring_spending_query += " AND rt.user_id = ?"
                recurring_spending_params.append(user_id)

            recurring_spending_query += """
                    UNION ALL

                    SELECT 
                        o.category_id,
                        o.amount,
                        o.original_date,
                        date(o.original_date, '+' || (iteration + 1) || ' month'),
                        iteration + 1
                    FROM occurrences o
                    WHERE date(o.original_date, '+' || (iteration + 1) || ' month') <= date(?)
                )
                SELECT c.name, SUM(o.amount)
                FROM occurrences o
                JOIN categories c ON o.category_id = c.id
                WHERE 1=1
            """

            if user_id:
                recurring_spending_query += " AND c.user_id = ?"

            if start_date and end_date:
                recurring_spending_query += (
                    " AND date(o.occurrence_date) BETWEEN date(?) AND date(?)"
                )
                recurring_spending_params.extend([end_date])
                if user_id:
                    recurring_spending_params.append(user_id)
                recurring_spending_params.extend([start_date, end_date])

                recurring_spending_query += " GROUP BY c.name"
                cursor.execute(recurring_spending_query, recurring_spending_params)
                recurring_spending = cursor.fetchall()
            else:
                recurring_spending = []

            # --- Combine both spendings ---
            spending_data = regular_spending + recurring_spending

            # --- Individual transactions ---
            transactions_query = """
                SELECT c.name, t.merchant, t.amount
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """
            transactions_params = []

            if user_id:
                transactions_query += " AND t.user_id = ? AND c.user_id = ?"
                transactions_params.extend([user_id, user_id])

            if start_date and end_date:
                transactions_query += """
                    AND date(t.date) BETWEEN date(?) AND date(?)
                """
                transactions_params.extend([start_date, end_date])
            transactions_query += """
                ORDER BY c.name, t.amount DESC
            """
            cursor.execute(transactions_query, transactions_params)
            regular_transactions = cursor.fetchall()

            # --- Recurring individual transactions ---
            recurring_transactions_query = """
                WITH RECURSIVE occurrences AS (
                    SELECT 
                        rt.category_id,
                        rt.merchant,
                        rt.amount,
                        rt.date as original_date,
                        date(rt.date, '+1 month') as occurrence_date,
                        1 as iteration
                    FROM recurringTransactions rt
                    WHERE rt.recurring = 1
            """

            recurring_transactions_params = []
            if user_id:
                recurring_transactions_query += " AND rt.user_id = ?"
                recurring_transactions_params.append(user_id)

            recurring_transactions_query += """
                    UNION ALL

                    SELECT 
                        o.category_id,
                        o.merchant,
                        o.amount,
                        o.original_date,
                        date(o.original_date, '+' || (iteration + 1) || ' month'),
                        iteration + 1
                    FROM occurrences o
                    WHERE date(o.original_date, '+' || (iteration + 1) || ' month') <= date(?)
                )
                SELECT c.name, o.merchant, o.amount
                FROM occurrences o
                JOIN categories c ON o.category_id = c.id
                WHERE 1=1
            """

            if user_id:
                recurring_transactions_query += " AND c.user_id = ?"

            if start_date and end_date:
                recurring_transactions_query += (
                    " AND date(o.occurrence_date) BETWEEN date(?) AND date(?)"
                )
                recurring_transactions_params.append(end_date)
                if user_id:
                    recurring_transactions_params.append(user_id)
                recurring_transactions_params.extend([start_date, end_date])

                cursor.execute(recurring_transactions_query, recurring_transactions_params)
                recurring_transactions = cursor.fetchall()
            else:
                recurring_transactions = []

            # --- Combine all transactions ---
            transactions_data = regular_transactions + recurring_transactions

            # --- SORT ---
            # Convert to DataFrames
            spending_df = pd.DataFrame(spending_data, columns=["Category", "Amount"])
            transactions_df = pd.DataFrame(
                transactions_data, columns=["Category", "Description", "Amount"]
            )

            # 1. Sort spending_data highest to lowest
            spending_sorted = (
                spending_df.groupby("Category")["Amount"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
            )

            # 2. Sort transactions_data:
            #    - First by category (using spending_data sorted order)
            #    - Then by amount within each category (highest to lowest)

            # Create a categorical type with the spending_sorted order
            category_order = pd.CategoricalDtype(
                categories=spending_sorted["Category"], ordered=True
            )
            transactions_df["Category"] = transactions_df["Category"].astype(category_order)

            # Sort by category (using the predefined order) and then by amount
            transactions_sorted = transactions_df.sort_values(
                ["Category", "Amount"], ascending=[True, False]
            )

            # Convert back to list of tuples if needed
            sorted_spending_list = list(spending_sorted.itertuples(index=False, name=None))
            sorted_transactions_list = list(
                transactions_sorted.itertuples(index=False, name=None)
            )

            return income_data, sorted_spending_list, sorted_transactions_list


    def get_current_netWorth_snapshot(self, user_id=None):
        """Retrieves the current net worth snapshot with all associated assets and liabilities"""
        try:
            with self._get_cursor() as cursor:
                # Get the current snapshot
                query = """
                    SELECT id, snapshot_date, created_at, note, 
                        total_assets, total_liabilities, net_worth
                    FROM net_worth_snapshots
                    WHERE is_current = 1
                """
                params = []

                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)

                query += " ORDER BY snapshot_date DESC LIMIT 1"

                cursor.execute(query, params)
                snapshot_data = cursor.fetchone()

                if not snapshot_data:
                    return None

                # Unpack the snapshot data
                (
                    snapshot_id,
                    snapshot_date,
                    created_at,
                    note,
                    total_assets,
                    total_liabilities,
                    net_worth,
                ) = snapshot_data

                # Get all items (assets and liabilities) for this snapshot
                cursor.execute(
                    """
                    SELECT name, type, category, amount, note
                    FROM net_worth_items
                    WHERE snapshot_id = ?
                    ORDER BY type DESC, amount DESC  -- Assets first, then liabilities
                    """,
                    (snapshot_id,),
                )
                items = cursor.fetchall()

                # Separate assets and liabilities
                assets = []
                liabilities = []

                for name, item_type, category, amount, note in items:
                    item = {
                        "name": name,
                        "type": category,  # Using category as the type (e.g., 'cash', 'loan')
                        "amount": amount,
                        "note": note or "",
                    }

                    if item_type == "asset":
                        assets.append(item)
                    else:
                        liabilities.append(item)

                return {
                    "snapshot_id": snapshot_id,
                    "snapshot_date": snapshot_date,
                    "created_at": created_at,
                    "note": note or "",
                    "total_assets": total_assets,
                    "total_liabilities": total_liabilities,
                    "net_worth": net_worth,
                    "assets": assets,
                    "liabilities": liabilities,
                }

        except Exception as e:
            print(f"Error fetching current net worth snapshot: {e}")
            return None


    def get_all_non_current_netWorth_snapshots(self, user_id=None):
        """Retrieves all non-current net worth snapshots with all associated assets and liabilities"""
        try:
            with self._get_cursor() as cursor:
                # Get all non-current snapshots ordered by date (newest first)
                query = """
                    SELECT id, snapshot_date, created_at, note, 
                        total_assets, total_liabilities, net_worth
                    FROM net_worth_snapshots
                    WHERE is_current = 0
                """
                params = []

                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)

                query += " ORDER BY snapshot_date DESC"

                cursor.execute(query, params)
                snapshots_data = cursor.fetchall()

                if not snapshots_data:
                    return []

                all_snapshots = []

                for snapshot_data in snapshots_data:
                    # Unpack the snapshot data
                    (
                        snapshot_id,
                        snapshot_date,
                        created_at,
                        note,
                        total_assets,
                        total_liabilities,
                        net_worth,
                    ) = snapshot_data

                    # Get all items (assets and liabilities) for this snapshot
                    cursor.execute(
                        """
                        SELECT name, type, category, amount, note
                        FROM net_worth_items
                        WHERE snapshot_id = ?
                        ORDER BY type DESC, amount DESC  -- Assets first, then liabilities
                        """,
                        (snapshot_id,),
                    )
                    items = cursor.fetchall()

                    # Separate assets and liabilities
                    assets = []
                    liabilities = []

                    for name, item_type, category, amount, note in items:
                        item = {
                            "name": name,
                            "type": category,  # Using category as the type (e.g., 'cash', 'loan')
                            "amount": amount,
                            "note": note or "",
                        }

                        if item_type == "asset":
                            assets.append(item)
                        else:
                            liabilities.append(item)

                    snapshot = {
                        "snapshot_id": snapshot_id,
                        "snapshot_date": snapshot_date,
                        "created_at": created_at,
                        "note": note or "",
                        "total_assets": total_assets,
                        "total_liabilities": total_liabilities,
                        "net_worth": net_worth,
                        "assets": assets,
                        "liabilities": liabilities,
                    }

                    all_snapshots.append(snapshot)

                return all_snapshots

        except Exception as e:
            print(f"Error fetching non-current net worth snapshots: {e}")
            return None


    def fetch_recent_income(
        self,
        search_term=None,
        start_date=None,
        end_date=None,
        num_income_limit=10,
        sort_order="default",
        user_id=None,
    ):
        with self._get_cursor() as cursor:
            query = """
                SELECT i.id, i.source, i.amount, i.date
                FROM income i
                WHERE 1=1
            """

            conditions = []
            params = []

            if user_id:
                conditions.append("i.user_id = ?")
                params.append(user_id)

            if search_term:
                conditions.append("i.source LIKE ?")
                params.append(f"%{search_term}%")

            if start_date or end_date:
                if start_date and end_date:
                    conditions.append("i.date BETWEEN ? AND ?")
                    params.extend([start_date, end_date])
                elif start_date:
                    conditions.append("i.date >= ?")
                    params.append(start_date)
                elif end_date:
                    conditions.append("i.date <= ?")
                    params.append(end_date)

            if conditions:
                query += " AND " + " AND ".join(conditions)

            if sort_order == "asc":
                query += " ORDER BY i.date ASC"
            elif sort_order == "desc":
                query += " ORDER BY i.date DESC"
            else:
                query += " ORDER BY i.id DESC"  # Default sorting

            query += f" LIMIT {num_income_limit}"

            cursor.execute(query, params)
            income = cursor.fetchall()

        return income


    def fetch_recent_transactions(
        self,
        search_term=None,
        category_filter=None,
        start_date=None,
        end_date=None,
        recurring_filter=None,
        tags_filter=None,
        num_trans_limit=10,
        sort_order="default",
        user_id=None,
    ):
        with self._get_cursor() as cursor:
            query = """
                SELECT t.id, c.name, t.merchant, t.amount, t.date, t.note, t.recurring
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """

            conditions = []
            params = []

            if user_id:
                conditions.append("t.user_id = ? AND c.user_id = ?")
                params.extend([user_id, user_id])
            
            if search_term:
                conditions.append("(t.merchant LIKE ? OR t.note LIKE ?)")
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            if category_filter:
                placeholders = ",".join(["?"] * len(category_filter))
                conditions.append(f"t.category_id IN ({placeholders})")
                params.extend(category_filter)
                
            if start_date or end_date:
                if start_date and end_date:
                    conditions.append("t.date BETWEEN ? AND ?")
                    params.extend([start_date, end_date])
                elif start_date:
                    conditions.append("t.date >= ?")
                    params.append(start_date)
                elif end_date:
                    conditions.append("t.date <= ?")
                    params.append(end_date)
                    
            if recurring_filter and "enable" in recurring_filter:
                conditions.append("t.recurring = 1")  # Only recurring transactions
            
            if tags_filter:
                
                tag_names = [tag['name'] for tag in tags_filter]
                
                if tag_names:
                    
                    tag_placeholders = ",".join(["?"] * len(tag_names))
                    
                    # Add condition to filter transactions that have at least one of the specified tags
                    conditions.append(f"tg.tag_name IN ({tag_placeholders})")
                    params.extend(tag_names)

            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            if sort_order == "asc":
                query += " ORDER BY t.date ASC"
            elif sort_order == "desc":
                query += " ORDER BY t.date DESC"
            else:
                query += " ORDER BY t.id DESC"  # Default sorting
                
            query += f" LIMIT {num_trans_limit}"
            
            cursor.execute(query, params)
            transactions = cursor.fetchall()

        return transactions

    def close(self):
        if self.use_pool:
            self.pool.close_all()
        else:
            if self._direct_conn:
                try:
                    self._direct_conn.commit()
                    self._direct_conn.close()
                    print("Direct connection closed")
                except Exception as e:
                    print(f"Error closing direct connection: {e}")

# --- Initialization ---

# Function to monitor pool health in the background
def monitor_pool_health(db: ExpenseDB, interval_seconds=60):
    """Background function to monitor pool health"""
    def monitor():
        while True:
            health = db.get_pool_health()
            if health['status'] in ['WARNING', 'CRITICAL']:
                print(f"⚠️  Pool Health Alert: {health['status']}")
                print(f"   Utilization: {health['utilization_percent']}%")
                print(f"   Active: {health['active_connections']}")
                print(f"   Failed Checkouts: {health['failed_checkouts']}")
            
            time.sleep(interval_seconds)
    
    # Run in background thread
    import threading
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

db_initialized = None  # Global variable to hold the initialized database instance
def init_db(use_pool_init=True, pool_size_init=8, enable_monitoring_init=True, use_wal_init=True):
    """
    Initialize the ExpenseDB instance
    
    Args:
        use_pool_init: Check to use connection pooling
        pool_size_init: Number of connections in pool
        enable_monitoring_init: Enable pool monitoring
        use_wal_init: Force WAL mode on/off (None = auto-detect)
    """
    global db_initialized
    if db_initialized is not None:
        raise RuntimeError("Database already initialized. Call cleanup() before re-initializing.")
    
    try:
        # Load configuration
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        # Get database path
        if config.getboolean("Database", "use_explicit_path"):
            db_name = config['Database']['name']
            db_path = config['Database'].get('path', '')
            DB_PATH = os.path.join(db_path, db_name) if db_path else os.path.join(
                os.path.dirname(os.path.abspath(__file__)), db_name
            )
        else:
            # Use file in folder
            DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_name)
        
        # Auto-detect Docker environment if WAL not specified
        if use_wal_init is None:
            # Check if running in Docker
            is_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER', False)
            use_wal_init = not is_docker  # Disable WAL in Docker by default
            
            if is_docker:
                print("Docker environment detected - using DELETE journal mode for better compatibility")
        
        db_initialized = ExpenseDB(
            DB_PATH,
            use_pool=use_pool_init, 
            pool_size=pool_size_init, 
            enable_monitoring=enable_monitoring_init,
            use_wal=use_wal_init
        )
        
        mode = "pooled" if use_pool_init else "direct"
        print(f"Database successfully loaded from {DB_PATH} ({mode} mode)")
        print(f"Journal mode: {'WAL' if use_wal_init else 'DELETE'}")
        
        # Start background health monitoring only for pooled mode (if needed)
        if use_pool_init and enable_monitoring_init:
            monitor_pool_health(db_initialized, interval_seconds=30)


        # ---------------------------------------------------------------------
        # Initialize Table creations if not exist TABLE CREATION METHODs
        
        # Tags - use if table missing
        db_initialized.create_tags_table() 

        # ---------------------------------------------------------------------
            
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    
    return db_initialized

def get_db():
    if db_initialized is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db_initialized

# Initialize database cleanup protocol
def cleanup():
    """Clean up database connections with proper WAL handling"""
    global db_initialized
    
    if db_initialized is None:
        print("No database to clean up")
        return
        
    print("Starting database cleanup...")
    start_time = time.time()
    
    try:
        db = db_initialized
        
        # Perform explicit checkpoint before closing
        if db.use_wal:
            if hasattr(db, 'perform_checkpoint'):
                print("Performing final checkpoint...")
                db.perform_checkpoint()
        
        if db.use_pool:
            # Close all connections explicitly
            if hasattr(db, 'pool') and hasattr(db.pool, 'close_all'):
                db.pool.close_all()
        
        # Clear the global reference
        db_initialized = None
        
        elapsed = time.time() - start_time
        print(f"Database cleanup completed in {elapsed:.2f} seconds")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        # Force clear the reference even on error
        db_initialized = None

# Docker-specific periodic checkpoint function
def periodic_checkpoint(db: ExpenseDB, interval_seconds=300):
    """
    Periodically checkpoint WAL file in Docker environments
    
    Args:
        db: ExpenseDB instance
        interval_seconds: Checkpoint interval (default 5 minutes)
    """
    def checkpoint_loop():
        while True:
            time.sleep(interval_seconds)
            try:
                db.perform_checkpoint()
                print(f"Periodic WAL checkpoint completed at {datetime.now()}")
            except Exception as e:
                print(f"Periodic checkpoint error: {e}")
    
    import threading
    checkpoint_thread = threading.Thread(target=checkpoint_loop, daemon=True)
    checkpoint_thread.start()
    return checkpoint_thread