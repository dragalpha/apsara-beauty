apsara-beauty/
│
├── README.md
├── .gitignore
├── .env.example
│
├── frontend/
│   ├── package.json                    # Frontend dependencies
│   ├── tsconfig.json                   # TypeScript config
│   ├── next.config.js                  # Next.js config
│   ├── .env.local                      # Frontend environment variables
│   │
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx              # Home page
│   │   │   ├── _app.tsx               # App wrapper
│   │   │   ├── _document.tsx          # Document wrapper
│   │   │   ├── analysis.tsx           # Skin analysis page
│   │   │   ├── recommendations.tsx    # Recommendations page
│   │   │   └── profile.tsx            # User profile
│   │   │
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── ImageUpload/
│   │   │   │   └── ImageUpload.tsx
│   │   │   ├── ProductCard/
│   │   │   │   └── ProductCard.tsx
│   │   │   └── Chat/
│   │   │       └── ChatBot.tsx
│   │   │
│   │   ├── styles/
│   │   │   ├── globals.css            # Global styles
│   │   │   ├── theme.ts               # Theme configuration
│   │   │   └── components/            # Component-specific styles
│   │   │
│   │   ├── utils/
│   │   │   ├── api.ts                 # API calls
│   │   │   └── helpers.ts             # Helper functions
│   │   │
│   │   └── hooks/
│   │       ├── useAuth.ts
│   │       └── useProducts.ts
│   │
│   └── public/
│       ├── favicon.ico
│       └── images/
│           └── logo.svg
│
├── backend/
│   ├── requirements.txt               # Python dependencies
│   ├── main.py                       # FastAPI app entry point
│   ├── .env                          # Backend environment variables
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── skin_analysis.py         # Skin analysis endpoints
│   │   ├── recommendations.py       # Recommendation endpoints
│   │   ├── auth.py                  # Authentication endpoints
│   │   └── products.py              # Product management endpoints
│   │
│   ├── ml_models/
│   │   ├── __init__.py
│   │   ├── skin_analyzer.py         # Skin analysis model
│   │   ├── recommendation_engine.py # Recommendation algorithm
│   │   └── train_models.py          # Model training scripts
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── connection.py            # Database connection
│   │   └── migrations/              # Alembic migrations
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── youtube_service.py       # YouTube API integration
│   │   ├── notification_service.py  # Notification system
│   │   └── image_service.py         # Image processing
│   │
│   └── utils/
│       ├── __init__.py
│       └── config.py                # Configuration settings
│
├── data/
│   ├── products/
│   │   └── products.csv             # Product database
│   └── models/
│       └── (trained model files)
│
└── docs/
    ├── API.md                       # API documentation
    └── SETUP.md                     # Setup instructions