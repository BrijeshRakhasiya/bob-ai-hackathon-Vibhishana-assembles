# How to Submit Your Hackathon Entry

Follow these steps to set up your submission repository correctly.
The judges depend on this structure to review your entry.

---

## Step 1  -  Create your repo from the official template

1. Go to [github.com/drijesh-ppatel/bob-ai-hackathon-submission-template](https://github.com/drijesh-ppatel/bob-ai-hackathon-submission-template)
2. Click the green **"Use this template"** button -> **"Create a new repository"**
3. Name your repository: **`bob-ai-hackathon-Vibhishana-assembles`**
4. Set visibility to **Public**
5. Click **Create repository**

---

## Step 2  -  Clone your repo locally

```bash
git clone https://github.com/[your-github-username]/bob-ai-hackathon-Vibhishana-assembles.git
cd bob-ai-hackathon-Vibhishana-assembles
```

---

## Step 3  -  Push the RouteGuard AI codebase

```bash
git add .
git commit -m "feat: complete RouteGuard AI submission  -  Vibhishana assembles"
git push origin main
```

---

## Step 4  -  Verify the GitHub Action passes

1. Go to your repo on GitHub
2. Click the **Actions** tab
3. Look for **Validate Submission**
4. Green status = submission is structurally complete
5. Red status = click the run, read the error, fix it, push again

---

## Step 5  -  Submit your repository URL

Once validation passes, submit via the official portal:  
[https://ibm.biz/bob-ai-charusat](https://ibm.biz/bob-ai-charusat)

**Deadline: 15 September 2026  -  12:00 PM to 11:45 PM IST**

---

## Checklist Before You Submit

- [x] `submission.yaml`  -  all required fields filled
- [x] `README.md`  -  no `[placeholder]` text remaining
- [x] `docs/problem-statement.md`  -  written
- [x] `docs/solution-overview.md`  -  written
- [x] `docs/architecture.md`  -  Mermaid diagram + explanation present
- [x] `docs/setup-guide.md`  -  tested end-to-end
- [x] `src/`  -  all source code committed, `.env.example` updated
- [ ] `demo/demo-video-link.txt`  -  **replace with your real video URL before submitting**
- [x] `demo/screenshots/`  -  3 screenshots present
- [x] `presentation/slides.html`  -  pitch deck present
- [ ] GitHub Actions **Validate Submission** workflow passes (green)
- [ ] Repository is **Public**
- [ ] Entry form submitted before the deadline

---

*IBM BoB AI Innovation Hackathon 2026  -  Team Vibhishana assembles  -  RouteGuard AI*
