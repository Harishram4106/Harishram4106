# Setting up your new profile README

Everything here goes into your profile repo: **github.com/Harishram4106/Harishram4106**.
The steps use the GitHub website, so you don't need git on your machine.

## What's in this folder

| File | What it is |
| --- | --- |
| `README.md` | The new profile page. It replaces your current one. |
| `assets/hero.svg` | Hero card with your name, roles, chips and the dot-matrix portrait (animated) |
| `assets/heatmap.svg` | Terminal-style contributions heatmap. It shows "booting" until the workflow first runs. |
| `assets/footer.svg` | Scrolling hex footer strip |
| `scripts/build_heatmap.py` | Rebuilds the heatmap from your real contributions |
| `scripts/build_stats.py` | Builds `assets/stats.svg`, `assets/streak.svg` and `assets/languages.svg` from your GitHub data |
| `scripts/build_hero.py` | Rebuilds the hero card, for example with a new photo or new title |
| `.github/workflows/profile-assets.yml` | Runs both scripts daily and commits the results under your name |

## Steps

1. **Open the repo** at https://github.com/Harishram4106/Harishram4106. Your old README stays in the commit history if you ever want it back.
2. **Upload the files.** Click **Add file → Upload files**. Drag in `README.md` and the `assets` and `scripts` folders, then click **Commit changes**. This replaces the old README.
3. **Add the workflow.** macOS hides folders that start with a dot, so create this one by hand:
   **Add file → Create new file**, name it exactly `.github/workflows/profile-assets.yml`, paste in the contents of that file from this folder, and commit.
4. **Let the workflow push.** Go to **Settings → Actions → General → Workflow permissions**, select **Read and write permissions**, and click **Save**.
5. **Run it once.** Open the **Actions** tab, pick **Profile assets**, and click **Run workflow**. About a minute later, `assets/heatmap.svg` shows your real contribution count and grid. After that it refreshes every day on its own.
6. **Check the snake.** The snake section reuses the `output` branch your current README already uses, so it keeps working as long as your existing snake workflow stays in the repo.

## Optional

- **Coding profiles.** If you're on LeetCode, GeeksforGeeks, HackerRank or CodeChef, open `README.md` and find the commented-out `coding-profiles.sh` block. Replace each `YOUR_HANDLE` with your username and delete the `<!--` and `-->` lines around it.
- **New photo or title.** Remove the photo's background first, then rebuild the hero card:
  ```bash
  pip install rembg pillow
  rembg i photo.jpg cutout.png
  python3 scripts/build_hero.py cutout.png
  ```
  The name, tagline and chips are set at the top of `scripts/build_hero.py`.

## Good to know

- The summary cards come from a free public service. Now and then it hits a rate limit and shows a broken image for a while. It fixes itself.
- The hero card animates on GitHub: the name types out, the portrait scans in and the cursor blinks. Animation is switched off for visitors who set their device to reduce motion.
