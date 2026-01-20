"""
Budgeteer Flask Application Factory
"""
from flask import Flask
from db import get_db


def create_app(config=None):
    """Application factory pattern for creating Flask app instances."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Configuration
    app.secret_key = config.get('SECRET_KEY', 'dev') if config else 'dev'
    
    # Initialize database
    _init_database()
    
    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.accounts import accounts_bp
    from app.routes.budgets import budgets_bp
    from app.routes.categories import categories_bp
    from app.routes.category_groups import category_groups_bp
    from app.routes.net_worth import net_worth_bp
    from app.routes.recurring import recurring_bp
    from app.routes.settings import settings_bp
    from app.routes.tags import tags_bp
    from app.routes.transactions import transactions_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(accounts_bp, url_prefix='/accounts')
    app.register_blueprint(budgets_bp, url_prefix='/budgets')
    app.register_blueprint(categories_bp, url_prefix='/categories')
    app.register_blueprint(category_groups_bp, url_prefix='/category-groups')
    app.register_blueprint(net_worth_bp, url_prefix='/net-worth')
    app.register_blueprint(recurring_bp, url_prefix='/recurring')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(tags_bp, url_prefix='/tags')
    app.register_blueprint(transactions_bp, url_prefix='/transactions')
    
    return app


def _init_database():
    """Initialize database schema and seed data."""
    with get_db() as db:
        db.executescript(open("schema.sql").read())
        db.execute("INSERT OR IGNORE INTO users(id, name) VALUES (1, 'You')")
        
        # Seed starter categories if DB is empty
        cur = db.execute("SELECT COUNT(*) c FROM categories")
        if cur.fetchone()["c"] == 0:
            db.executemany(
                "INSERT INTO categories(name) VALUES (?)",
                [
                    (x,)
                    for x in [
                        "Rent/Mortgage",
                        "Utilities",
                        "Groceries",
                        "Dining",
                        "Transport",
                        "Health",
                        "Subscriptions",
                        "Entertainment",
                        "Misc",
                    ]
                ],
            )
        
        # Seed one debit account if none
        cur = db.execute("SELECT COUNT(*) c FROM accounts")
        if cur.fetchone()["c"] == 0:
            db.execute("INSERT INTO accounts(name, type) VALUES ('My Debit', 'debit')")
