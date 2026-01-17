"""
DICOM Gateway Application - Clean Architecture
Main application entry point with Flask and Flask-RestX setup
"""
from flask import Flask, render_template
from flask_restx import Api

from core.config import Config
from core.logger import setup_logger
from routes.dicom_routes import dicom_ns, satset_ns

# Initialize configuration
Config.init_app()

# Setup logger
logger = setup_logger()

# Create Flask app
app = Flask(__name__, template_folder='templates')

# Setup Flask-RestX API
api = Api(
    app,
    version='1.1',
    title='DICOM Gateway API',
    doc='/api/docs',
    prefix='/api'
)

# Register namespaces
api.add_namespace(dicom_ns)
api.add_namespace(satset_ns)

# Web UI route
@app.route("/")
def index():
    """Serve main HTML page"""
    return render_template("dcmpage.html")

if __name__ == '__main__':
    logger.info("Starting DICOM Gateway Application...")
    app.run(host='0.0.0.0', port=5000, debug=False)