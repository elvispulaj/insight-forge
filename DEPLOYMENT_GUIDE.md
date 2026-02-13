# Deploying InsightForge to the Web 🚀

This guide explains how to deploy your **InsightForge** application so anyone with the link can use it. We will use **Streamlit Community Cloud**, which is free, easy, and connects directly to your GitHub repository.

---

## Part 1: Push Code to GitHub

First, your code needs to be on GitHub. If you haven't already:

1.  **Create a Repository**:
    - Go to [GitHub.com](https://github.com) and create a **New Repository**.
    - Name it `insight-forge` (or similar).
    - Select **Public** (easiest) or Private.
    - **Do NOT** add a README or .gitignore yet (you have them locally).

2.  **Push Your Local Code**:
    - Open your terminal/command prompt in the project folder:
      `c:\Users\elvis\OneDrive\Courses\Perdue\GEN AI\Capstone project\Antigravity InsightForge`
    - Run these commands:
      ```bash
      git init
      git add .
      git commit -m "Initial commit for deployment"
      git branch -M main
      git remote add origin https://github.com/YOUR_USERNAME/insight-forge.git
      git push -u origin main
      ```
    *(Replace `YOUR_USERNAME` with your actual GitHub username)*

---

## Part 2: Deploy on Streamlit Cloud

1.  **Sign Up / Login**:
    - Go to [share.streamlit.io](https://share.streamlit.io).
    - Click **Sign in** and authorize with your **GitHub account**.

2.  **Deploy App**:
    - Click the **"New app"** button.
    - **Repository**: Select your `insight-forge` repo.
    - **Branch**: Select `main`.
    - **Main file path**: Enter `app.py`.
    - Click **"Deploy!"**. 🎈

3.  **Wait for Build**:
    - Streamlit will now install everything listed in your `requirements.txt`.
    - This might take 2-3 minutes. Watch the logs on the right side.

---

## Part 3: Handling Secrets (Optional)

By default, your app asks users to input their own OpenAI API Key in the sidebar. This is perfect for a public demo!

However, if you want to provide a **default key** (so users don't have to enter one), follow these steps:

1.  On your deployed Streamlit app dashboard, click **"Manage app"** (bottom right) or the **three dots** -> **Settings**.
2.  Go to the **Secrets** section.
3.  Paste your API key like this:
    ```toml
    OPENAI_API_KEY = "sk-proj-..."
    ```
4.  Click **Save**.
5.  *Security Warning: If your repo is public, do NOT commit your .env file containing the key. Use Streamlit Secrets only.*

---

## Part 4: Share It!

Once deployed, you will get a URL like:
`https://insight-forge.streamlit.app`

- **Send this link** to anyone.
- They can open it on their phone or laptop.
- Since standard Streamlit cloud apps are public, anyone with the link can view it.
- **Important:** Users must create an account and log in to access the dashboard and features.

---

### Troubleshooting

- **"Module not found" error?**
  - Check your `requirements.txt`. Every library imported in `app.py` must be listed there.
- **"File not found" error?**
  - Ensure any data files (like `styles.css`) are included in your GitHub repo and not ignored by `.gitignore`.
- **App falls asleep?**
  - Free apps go to sleep after inactivity. Just click the "Wake up" button to restart it.
