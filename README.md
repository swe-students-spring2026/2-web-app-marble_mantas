# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

PantryPal is a simple, mobile-friendly web application that helps users track pantry inventory and manage grocery shopping efficiently to reduce food waste and avoid duplicate purchases.

## User stories

[Link to the list of user stories.](https://github.com/swe-students-spring2026/2-web-app-marble_mantas/issues/2)

## Steps necessary to run the software

Make sure you have the following installed:

- Python 3.10+
- Pipenv
- Docker (can be installed [here](https://www.docker.com/products/docker-desktop/))

You can install Pipenv with:

```bash
pip install pipenv
```

---

### 1. Clone the Repository & Go to Directory

```bash
git clone https://github.com/swe-students-spring2026/2-web-app-marble_mantas.git
cd 2-web-app-marble_mantas
```

---
### 2. Install Dependencies (Using Pipfile)

Since this project includes a `Pipfile`, install all dependencies with:

```bash
pipenv install
```

Then activate the virtual environment:

```bash
pipenv shell
```

---

### 3. Configure Environment Variables

Rename the example environment file:

Mac / Linux:

```bash
mv env.example .env
```

Windows (Powershell):

```powershell
rename env.example .env
```

You can manually change the name too.
Make sure your `.env` file contains the correct configuration values.

---

### 4. Start MongoDB with Docker

```bash
docker run -d -p 27017:27017 --name pantrypal-mongo mongo
```
To verify the container is running:

```bash
docker ps
```

---

### 5. Run the Flask Application

```bash
flask run
```

---

### 6. Open in Browser

Visit:

```
http://127.0.0.1:5000
```

---

### Troubleshooting

- Make sure Docker is running.
- Make sure Docker container is running.
- Make sure your `.env` file exists.
- If port `27017` is already in use, stop any existing MongoDB instances, or configure `.env` to use a different port, and set up MongoDB using that port.
- If Flask does not start, ensure you activated the pipenv shell.
- If port `5000` is already in use causing a 403 error, do `flask run --port=5001` and visit `http://127.0.0.1:5001` instead.

### Stopping the Application

To stop the Docker container:

```bash
docker stop mongodb_pantrypal
```

To remove the container:

```bash
docker rm mongodb_pantrypal
```

## Task boards

[Link to the Sprint 1 task board.](https://github.com/orgs/swe-students-spring2026/projects/7/views/1)

[Link to the Sprint 1 task board.](https://github.com/orgs/swe-students-spring2026/projects/46/views/1)
