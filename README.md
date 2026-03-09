# Meal Plan Recommendation System

An intelligent meal planning system that generates personalized dining recommendations based on calorie goals, meal preferences, and dining hall availability.

## Features

- **Smart Recommendations**: Algorithm optimizes for nutrition balance and variety
- **Real Dining Data**: Web scraper fetches live menu information
- **Calorie Tracking**: Set daily limits and customize meal ratios
- **Modern Web Interface**: Professional Flask-based frontend
- **Multiple Options**: Generate alternative meal plans per time slot
- **Hall Preferences**: Choose preferred dining locations

## Quick Start

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd meal_plan_rec

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m db.seed
```

### Running the Application

```bash
# Start the Flask web server
python web/app.py

# Or use the module approach
python -m web.app
```

Then open your browser to: **http://localhost:5000**

## Project Structure

```
meal_plan_rec/
├── app/                    # Business logic
│   ├── categorizer.py     # Food categorization system
│   ├── recommender.py     # Meal recommendation algorithm
│   ├── scraper.py         # Web scraping for menu data
│   ├── overrides.py       # Manual data corrections
│   └── services/          # Service layer
├── db/                     # Database layer
│   ├── database.py        # SQLAlchemy setup
│   ├── models.py          # Database models
│   ├── repositories.py    # Data access layer
│   └── seed.py            # Database initialization
├── web/                    # Web application
│   ├── app.py             # Flask application
│   └── templates/         # HTML templates
├── tests/                  # Test suite
├── data/                   # Data files
└── requirements.txt        # Python dependencies
```

## Usage

### Web Interface

1. **Select Meal Times**: Choose which meals you want (Breakfast, Lunch, Dinner)
2. **Set Preferences**:
   - Daily calorie limit (1000-4000)
   - Calorie split per meal (optional, must total 100%)
   - Preferred dining halls
   - Number of options per meal
3. **Generate Plan**: Click "Generate Meal Plan" to get AI-powered recommendations

### API Endpoints

- `GET /` - Main form page
- `POST /recommendations` - Generate meal plan
- `GET /health` - Health check endpoint

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Jinja2 templates
- **Database**: SQLite
- **Scraping**: BeautifulSoup, Requests
- **ML/Data**: Pandas, NumPy, Sentence Transformers
- **Testing**: Pytest

## Development

### Running Tests

```bash
pytest tests/ -v
```



## Algorithm Overview

The recommendation system uses a multi-stage approach:

1. **Data Collection**: Scrapes dining hall websites for current menus
2. **Categorization**: ML-based classification of dishes into food types
3. **Optimization**: Generates meal combinations that:
   - Meet calorie targets (±buffer)
   - Balance nutrition (proteins, bases, sides, beverages)
   - Maximize variety
   - Respect dietary preferences
4. **Ranking**: Scores options based on freshness and user history

## Future Enhancements

- [ ] Dietary restriction filters (vegetarian, vegan, gluten-free, etc.)
- [ ] User accounts and meal history
- [ ] Nutritional breakdown (macros, vitamins, etc.)
- [ ] Mobile app
- [ ] Social features (share plans, ratings)
- [ ] Integration with campus meal plan systems




## Author

Philip Perry Pearce-Pearson and IyiOluwa Adaramola

## Acknowledgments

- Denison University Dining Services for menu data
- Sentence Transformers for NLP capabilities