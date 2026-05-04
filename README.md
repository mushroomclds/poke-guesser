# PokeTCG-Guesser


## Game Description

PokeApp is a Pokémon TCG card guessing game. The app fetches real Pokémon Trading Card Game data using the [Pokémon TCG API](https://docs.pokemontcg.io/).

**How to Play:**
- You are shown a random Pokémon card (or a selection to choose from), but the card's name and image are blurred out.
- Try to guess the Pokémon! With each incorrect guess, more letters of the name are revealed or the image becomes less blurred.
- You have a total of 5 tries to guess correctly.

**Future Game Modes:**
- High/Low: Guess if the next card's price is higher or lower.
- Guess the price of a card.
- Guess the rarity, type, or set of a card.

> **Note:** This application is for educational and portfolio project purposes ONLY.


This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 19.2.8.

## Development server

To start a local development server, run:

```bash
ng serve
```

Once the server is running, open your browser and navigate to `http://localhost:4200/`. The application will automatically reload whenever you modify any of the source files.


## Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.


## Current Status
Currently I only have the below done. Gets 3 random cards given pokemon name and outputs price
![alt text](image.png)



## Here’s a concise, high-level summary of the backend architecture and technologies for your web app:

---

## Backend Architecture Overview

The backend is structured as a modular Python Flask application, organized for scalability and maintainability. It follows a layered architecture with clear separation of concerns:

- **Entry Point**: main.py initializes and runs the Flask app.
- **App Package**: Contains all core logic, split into submodules:
  - **models/**: Defines ORM models (e.g., User) for database interaction.
  - **routes/**: Houses API endpoints, authentication, and game session logic.
  - **services/**: Business logic and service classes (e.g., user management).
  - **utils/**: Utility functions for authentication, logging, and database connections.
- **Database**: Interacts with an Oracle database, with connection utilities and table creation scripts.
- **Configuration**: Centralized in config.py for environment and app settings.
- **Logging**: Custom logging utilities for monitoring and debugging.
- **Testing**: test.py for backend unit tests.

### Request Flow

1. **Client Request** → Flask API endpoint (routes/)
2. **Authentication/Validation** (utils/auth_decorator.py)
3. **Business Logic** (services/)
4. **Database Access** (models/, utils/oracle_db.py)
5. **Response** → Client

### Technologies Used

- **Python 3**
- **Flask** (web framework)
- **Oracle Database** (via cx_Oracle or similar)
- **Custom Logging**
- **Modular Python Packages**

---
