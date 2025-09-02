# GitHub Secrets Configuration for Heroku Deployment

## How to Add Secrets to GitHub

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name and value listed below

## Required GitHub Secrets

Copy and paste these values from your `.env` file:

### 🔴 CRITICAL - Heroku Configuration
| Secret Name | Value | Description |
|------------|-------|-------------|
| `HEROKU_API_KEY` | Get from https://dashboard.heroku.com/account | Your Heroku API key |
| `HEROKU_EMAIL` | Your Heroku email | Email used for Heroku account |
| `HEROKU_APP_NAME` | Your app name | Name of your production Heroku app |
| `HEROKU_STAGING_APP_NAME` | Your staging app name | Name of your staging Heroku app (optional) |

### 🟡 Django Configuration
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `DJANGO_SECRET_KEY` | `f3b1a2e7c9d8f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0` | Django secret key |

### 🟢 Supabase Configuration (Development)
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `SUPABASE_URL` | `https://dndfnoyltoqzrbnuxafz.supabase.co` | Supabase project URL |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRuZGZub3lsdG9xenJibnV4YWZ6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUyNTk5NjgsImV4cCI6MjA3MDgzNTk2OH0.m2fMTBMTyrJl6rWEiXrGNXYaTgaGEx8xPK6rdx474wk` | Supabase anonymous key |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRuZGZub3lsdG9xenJibnV4YWZ6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTI1OTk2OCwiZXhwIjoyMDcwODM1OTY4fQ.RpajbqdaTcCqtXkxVpkK1P-Rj1DzaS4-YQiY1PGpwQM` | Supabase service role key |
| `SUPABASE_JWT_SECRET` | `sia1zy6U6Pf1MGfy3A0N+zEaYa9u758nXX2YWoYj/O8c4F2a1K1P+be+hoL35NY6sLXDWg7BzVa7XpRt3249TA==` | Supabase JWT secret |
| `SUPABASE_WEBHOOK_SECRET` | `your-webhook-secret-here` | Update with actual webhook secret |

### 🔵 Database Configuration
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `DATABASE_URL` | `postgresql://postgres.dndfnoyltoqzrbnuxafz:QnOHiIk2YZYP0gPl@aws-1-us-west-1.pooler.supabase.com:5432/postgres` | PostgreSQL connection URL |

### 💳 Stripe Configuration
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `STRIPE_SECRET_KEY` | `sk_test_51RebMZ2fB4WJ1ELeaODI5daCll3rpXMPQ9F8isEmCEuRRq8v8t2c9E3IFLzoMqRlYdYjpfd6SQ1yb3bnID0sZnu3002Bn1sBAx` | Stripe secret key |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_51RebMZ2fB4WJ1ELeiZQXVTkzG3TZFKJpzmvD2QHc5rAwM16TSUcBMe1NDoENz1d1aeKmthsIWfGOKLUsAd8wvW4R00JRu8RYP4` | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | `whsec_vG6Ojl3CPbLOiVZedWg1skGYh5IdhzUP` | Stripe webhook secret |

### 🤖 OpenAI Configuration
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `OPENAI_API_KEY` | `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` | OpenAI API key |

### 📦 Backblaze Configuration
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `BACKBLAZE_KEY_ID` | `0022aa493f0b93f0000000001` | Backblaze key ID |
| `BACKBLAZE_APPLICATION_KEY` | `K002tqaSq0yUCdbbwnr6D5G5x1JHGmU` | Backblaze application key |
| `BACKBLAZE_BUCKET_ID` | `b20a0a2459434f709b49031f` | Backblaze bucket ID |
| `BACKBLAZE_BUCKET_NAME` | `unpuzzle` | Backblaze bucket name |

### 🔄 Redis Configuration
| Secret Name | Value from .env | Description |
|------------|-----------------|-------------|
| `REDIS_URL` | `redis://127.0.0.1:6379/1` | Note: You'll need to use Heroku Redis addon URL in production |

### ☁️ Cloudflare (Optional - not in your .env)
| Secret Name | Value | Description |
|------------|-------|-------------|
| `CLOUDFLARE_ACCOUNT_ID` | Leave empty or add if you have | Cloudflare account ID |
| `CLOUDFLARE_API_TOKEN` | Leave empty or add if you have | Cloudflare API token |

## Quick Copy Script

You can use this bash script to set all secrets at once using GitHub CLI:

```bash
# Install GitHub CLI first: https://cli.github.com/

# Set your repository
REPO="your-username/unpuzzle-mvp"

# Add all secrets
gh secret set DJANGO_SECRET_KEY --repo $REPO --body "f3b1a2e7c9d8f4a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0"
gh secret set SUPABASE_URL --repo $REPO --body "https://dndfnoyltoqzrbnuxafz.supabase.co"
gh secret set SUPABASE_ANON_KEY --repo $REPO --body "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRuZGZub3lsdG9xenJibnV4YWZ6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTUyNTk5NjgsImV4cCI6MjA3MDgzNTk2OH0.m2fMTBMTyrJl6rWEiXrGNXYaTgaGEx8xPK6rdx474wk"
gh secret set SUPABASE_SERVICE_KEY --repo $REPO --body "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRuZGZub3lsdG9xenJibnV4YWZ6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NTI1OTk2OCwiZXhwIjoyMDcwODM1OTY4fQ.RpajbqdaTcCqtXkxVpkK1P-Rj1DzaS4-YQiY1PGpwQM"
gh secret set SUPABASE_JWT_SECRET --repo $REPO --body "sia1zy6U6Pf1MGfy3A0N+zEaYa9u758nXX2YWoYj/O8c4F2a1K1P+be+hoL35NY6sLXDWg7BzVa7XpRt3249TA=="
gh secret set DATABASE_URL --repo $REPO --body "postgresql://postgres.dndfnoyltoqzrbnuxafz:QnOHiIk2YZYP0gPl@aws-1-us-west-1.pooler.supabase.com:5432/postgres"
gh secret set STRIPE_SECRET_KEY --repo $REPO --body "sk_test_51RebMZ2fB4WJ1ELeaODI5daCll3rpXMPQ9F8isEmCEuRRq8v8t2c9E3IFLzoMqRlYdYjpfd6SQ1yb3bnID0sZnu3002Bn1sBAx"
gh secret set STRIPE_PUBLISHABLE_KEY --repo $REPO --body "pk_test_51RebMZ2fB4WJ1ELeiZQXVTkzG3TZFKJpzmvD2QHc5rAwM16TSUcBMe1NDoENz1d1aeKmthsIWfGOKLUsAd8wvW4R00JRu8RYP4"
gh secret set STRIPE_WEBHOOK_SECRET --repo $REPO --body "whsec_vG6Ojl3CPbLOiVZedWg1skGYh5IdhzUP"
gh secret set OPENAI_API_KEY --repo $REPO --body "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"
gh secret set BACKBLAZE_KEY_ID --repo $REPO --body "0022aa493f0b93f0000000001"
gh secret set BACKBLAZE_APPLICATION_KEY --repo $REPO --body "K002tqaSq0yUCdbbwnr6D5G5x1JHGmU"
gh secret set BACKBLAZE_BUCKET_ID --repo $REPO --body "b20a0a2459434f709b49031f"
gh secret set BACKBLAZE_BUCKET_NAME --repo $REPO --body "unpuzzle"
gh secret set REDIS_URL --repo $REPO --body "redis://127.0.0.1:6379/1"
```

## Important Notes

⚠️ **SECURITY WARNING**: 
- These are sensitive credentials from your `.env` file
- Never commit these values to your repository
- Consider rotating these keys after setup
- Use different keys for production vs development

🔒 **For Production**:
- Generate a new `DJANGO_SECRET_KEY` using: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- Use production Supabase instance credentials (commented out in your .env)
- Use Stripe live keys instead of test keys
- Get Redis URL from Heroku addon after creating it

📝 **Next Steps**:
1. Add all these secrets to GitHub
2. Get Heroku API key and add `HEROKU_API_KEY`, `HEROKU_EMAIL`, `HEROKU_APP_NAME`
3. Create Heroku app: `heroku create your-app-name`
4. Push your code to trigger deployment

## Verification

After adding secrets, verify they're set:
```bash
gh secret list --repo your-username/unpuzzle-mvp
```

## Heroku-Specific Environment Variables

These will be automatically set by the GitHub Action, but you can also set them manually on Heroku:

```bash
heroku config:set KEY=value -a your-app-name
```