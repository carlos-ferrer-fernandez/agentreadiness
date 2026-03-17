# Deploy AgentReadiness Online - Easy Guide

This guide will help you deploy the AgentReadiness platform online so customers can access it from anywhere.

## 📁 First: Get Your Files

Before you start, you need the code files. Here's how to get them:

### Option 1: Download from the KIMI_REF tag below
At the bottom of this conversation, you'll see a file reference. Click on it to download all the files as a ZIP.

### Option 2: Ask me to send you the files
Just say "send me the files" and I'll provide them in a way you can download.

### Option 3: Copy files manually
If you have access to the files, make sure you have the entire `agentreadiness` folder.

---

Once you have the files, follow the steps below!

## Option 1: Railway (Easiest - Recommended) ⭐

Railway is the easiest way to deploy. It's like a "one-click" deploy.

### Step 1: Create Accounts

1. **GitHub Account** (if you don't have one)
   - Go to https://github.com/signup
   - Create a free account

2. **Railway Account**
   - Go to https://railway.app
   - Click "Login" and sign in with your GitHub account

### Step 2: Upload Your Code to GitHub (Drag & Drop!)

**Option A: Using the files I provided**

1. Create a new repository on GitHub:
   - Go to https://github.com/new
   - Name it "agentreadiness"
   - Click "Create repository"

2. On the repository page, you'll see "...or drag and drop files here"

3. **Download the files from me** - I'll give you a ZIP file with all the code

4. **Unzip** the file on your computer

5. **Open the folder** and select ALL files inside

6. **Drag and drop** them into the GitHub page

7. Type "Initial commit" in the message box

8. Click **"Commit changes"**

✅ Done! Your code is now on GitHub.

**Option B: If you want to use command line (advanced)**

If you're comfortable with the terminal, you can also use git commands. See `DEPLOYMENT-ADVANCED.md` for that method.

### Step 3: Deploy on Railway

1. Go to https://railway.app/new

2. Click "Deploy from GitHub repo"

3. Select your "agentreadiness" repository

4. Railway will automatically detect your services and deploy them

5. **Add Environment Variables**:
   - Click on your project
   - Go to "Variables" tab
   - Add these variables:
   
   | Variable | Value | Where to Get It |
   |----------|-------|-----------------|
   | `OPENAI_API_KEY` | sk-... | https://platform.openai.com/api-keys |
   | `STRIPE_SECRET_KEY` | sk_test_... | https://dashboard.stripe.com/test/apikeys |
   | `STRIPE_PUBLISHABLE_KEY` | pk_test_... | https://dashboard.stripe.com/test/apikeys |
   | `JWT_SECRET` | any-random-text | Just type 32 random characters |

6. **Get Your Website URL**:
   - Railway will give you a URL like `https://agentreadiness-production.up.railway.app`
   - This is your live website! 🎉

---

## Option 2: Render (Also Easy)

Render is another simple option with a free tier.

### Step 1: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub

### Step 2: Create render.yaml

Create a file named `render.yaml` in your project root:

```yaml
services:
  - type: web
    name: agentreadiness-web
    runtime: node
    buildCommand: cd apps/web && npm install && npm run build
    startCommand: cd apps/web && npm run preview
    envVars:
      - key: VITE_API_URL
        value: https://agentreadiness-api.onrender.com

  - type: web
    name: agentreadiness-api
    runtime: python
    buildCommand: cd apps/api && pip install -r requirements.txt
    startCommand: cd apps/api && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: STRIPE_SECRET_KEY
        sync: false
      - key: STRIPE_PUBLISHABLE_KEY
        sync: false
      - key: JWT_SECRET
        sync: false
```

### Step 3: Deploy

1. Upload your code to GitHub (same drag & drop method as Railway Step 2)

2. In Render dashboard:
   - Click "New +"
   - Select "Blueprint"
   - Connect your GitHub repo

3. Render will automatically deploy both frontend and backend

---

## Setting Up Stripe Payments (Required for Paid Plans)

To accept payments, you need a Stripe account:

### Step 1: Create Stripe Account

1. Go to https://stripe.com
2. Click "Start now" and create an account
3. Complete the onboarding (takes 5 minutes)

### Step 2: Get API Keys

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy the "Secret key" (starts with `sk_test_`)
3. Copy the "Publishable key" (starts with `pk_test_`)

### Step 3: No Product Creation Needed!

Pricing is **dynamic** — it scales with the documentation size (3x our AI analysis cost, min €49).
The app uses Stripe's `price_data` to create the correct amount at checkout time automatically.

You do NOT need to create any Products or Prices in Stripe. Just the API keys are enough.

### Step 4: Add to Environment Variables

Add these to your Railway/Render environment variables:

```
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
```

---

## Setting Up OpenAI (Required for Analysis)

The AI analysis needs an OpenAI API key:

1. Go to https://platform.openai.com/signup
2. Create an account
3. Go to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. Add to your environment variables as `OPENAI_API_KEY`

**Note**: OpenAI charges for API usage. New accounts get $5 free credit. After that, expect to pay ~$1-5 per analysis depending on documentation size.

---

## Custom Domain (Optional)

Want your own domain like `agentreadiness.yourcompany.com`?

### Using Railway:

1. Buy a domain from https://namecheap.com or https://godaddy.com
2. In Railway, go to your service settings
3. Click "Custom Domain"
4. Enter your domain
5. Railway will give you DNS records to add
6. Go to your domain provider and add those DNS records
7. Wait 10-30 minutes for it to work

### Using Render:

Same process as Railway - go to service settings and add custom domain.

---

## Checking If Everything Works

After deployment, test these URLs:

1. **Homepage**: `https://your-url.com`
   - Should show the landing page with the assessment form

2. **API Health**: `https://your-url.com/api/health`
   - Should show `{"status": "healthy"}`

3. **Run an Assessment**:
   - Enter any docs URL (like `docs.stripe.com`)
   - Should complete in 30-60 seconds
   - Should show score and results

---

## Troubleshooting

### "Build Failed" Error

**Problem**: The deployment didn't work.

**Solution**:
1. Check the build logs in Railway/Render
2. Make sure all environment variables are set
3. Try redeploying

### "Payment Not Working"

**Problem**: Customers can't pay.

**Solution**:
1. Check that all Stripe environment variables are correct
2. Make sure you're using TEST keys (not live keys yet)
3. In test mode, use card number `4242 4242 4242 4242` with any future expiry date

### "Assessment Stuck"

**Problem**: Assessment never finishes.

**Solution**:
1. Check that `OPENAI_API_KEY` is set correctly
2. Check that you have credit in your OpenAI account
3. Check the API logs for errors

---

## Going Live (Accepting Real Payments)

When you're ready to accept real customer payments:

### Step 1: Switch to Live Stripe Keys

1. In Stripe Dashboard, toggle from "Test mode" to "Live mode"
2. Get your live API keys
3. Update environment variables with live keys
4. Redeploy

### Step 2: Pricing is Automatic

Pricing is dynamic and calculated automatically (3x API cost, min €49).
No Stripe products to update — the amount is set at checkout time.

### Step 3: Test Real Payment

1. Use a real credit card
2. Make a small test purchase
3. Check that you receive the money in Stripe

---

## Monthly Costs Estimate

| Service | Cost | Notes |
|---------|------|-------|
| Railway/Render | $0-20/month | Free tier available |
| OpenAI API | $1-50/month | Depends on usage |
| Stripe | 2.9% + 30¢ per transaction | Only when you make sales |
| Domain | $10-15/year | Optional |

**Total**: ~$20-70/month for a small startup

---

## Need Help?

- **Railway Docs**: https://docs.railway.app
- **Render Docs**: https://render.com/docs
- **Stripe Docs**: https://stripe.com/docs
- **Email us**: support@agentreadiness.dev

---

## Quick Checklist

Before going live, make sure:

- [ ] Downloaded the files (from KIMI_REF below or ask me)
- [ ] Uploaded files to GitHub (drag & drop)
- [ ] Deployed on Railway or Render
- [ ] OPENAI_API_KEY is set
- [ ] Stripe account created
- [ ] Stripe products created
- [ ] All Stripe environment variables set
- [ ] Tested the assessment flow
- [ ] Tested the payment flow
- [ ] Custom domain configured (optional)

**You're ready to launch! 🚀**
