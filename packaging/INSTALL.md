# Installing Marketing Intelligence Studio

No technical knowledge needed — no Python, no GitHub, no command line.

## 1. Get the folder

You should have a folder called **"Marketing Intelligence Studio"** (Windows)
or a file called **"Marketing Intelligence Studio.app"** alongside a
`clients` folder and a `.env.example` file (macOS). If you received a `.zip`
file, double-click it first to unzip everything into one folder, then keep
that whole folder together — don't move just the app by itself.

## 2. Add your Reddit credentials (one-time setup)

Reddit Research needs a Reddit API key to search Reddit. This is free and
takes about 2 minutes:

1. Go to https://www.reddit.com/prefs/apps in your browser (log into Reddit
   first if needed).
2. Click **"create app"** (or "create another app").
3. Fill in:
   - **name**: anything, e.g. "Marketing Intelligence Studio"
   - **type**: choose **script**
   - **redirect uri**: `http://localhost:8080` (required by the form, not
     actually used)
4. Click **"create app"**. You'll see two values you need:
   - **client ID** — the string right under the app name/"personal use
     script"
   - **secret** — labeled "secret"
5. In the folder from step 1, find the file named **`.env.example`**. Make a
   copy of it and rename the copy to **`.env`** (just `.env`, nothing else —
   on Windows, if you don't see the `.example` part, turn on "File name
   extensions" in File Explorer's View tab first).
6. Open `.env` in Notepad (Windows) or TextEdit (Mac) and fill in the two
   values you copied:

   ```
   REDDIT_CLIENT_ID=paste_your_client_id_here
   REDDIT_CLIENT_SECRET=paste_your_secret_here
   ```
7. Save the file and close it.

**One team member can do this once and share the resulting `.env` file with
the rest of the team** — everyone can use the same Reddit app credentials.

## 3. Launch the app

- **Windows**: open the "Marketing Intelligence Studio" folder and
  double-click **`Marketing Intelligence Studio.exe`**.
  - If Windows shows "Windows protected your PC" (SmartScreen, because this
    app isn't yet from a registered publisher): click **"More info"**, then
    **"Run anyway"**. This only appears the first time.
- **macOS**: double-click **`Marketing Intelligence Studio.app`**.
  - If macOS says the app "cannot be opened because it is from an
    unidentified developer": right-click (or Control-click) the app, choose
    **"Open"**, then confirm **"Open"** in the dialog. This only appears the
    first time.

The app window opens with Reddit Research already selected.

## 4. Use it

1. **Pick a client** from the list on the left.
2. **Type a topic** in the box (e.g. "pricing", "reliability").
3. **Click Run** (or press Enter).

A report appears in a few seconds. Then:

- **Save for NotebookLM** — saves a clean copy of the report for your
  team's knowledge base.
- **Open Export Folder** — opens the folder containing that saved file.
- **Copy Report** — copies the report so you can paste it elsewhere.

Drag the saved file into NotebookLM and you're done.

## Troubleshooting

- **"Reddit research failed: Missing Reddit API credentials"** — the `.env`
  file isn't set up correctly. Re-check step 2: the file must be named
  exactly `.env` (not `.env.txt` or `.env.example`) and sit in the same
  folder as the app.
- **The app won't open at all** — make sure you kept the whole folder
  together after unzipping (Windows) rather than moving just the `.exe` by
  itself; it needs the files next to it to run.
- **Nothing happens when I click Run** — check that a client is selected in
  the list on the left (the topic box only works once one is).

Anything else, contact whoever set this up for your team.
