from app import create_app
import os
import sys

app = create_app()

if __name__ == '__main__':
    # Development server settings
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=debug_mode
    )