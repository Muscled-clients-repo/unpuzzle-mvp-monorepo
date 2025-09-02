# Heroku Deployment Guide

## Prerequisites

1. **Heroku Account**: Sign up at https://heroku.com
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Heroku CLI** (optional for local testing): https://devcenter.heroku.com/articles/heroku-cli

## Setup Instructions

### 1. Create Heroku App

```bash
# Login to Heroku
heroku login

# Create a new Heroku app
heroku create your-app-name

# For staging environment
heroku create your-app-name-staging
```

### 2. Get Heroku API Key

1. Go to https://dashboard.heroku.com/account
2. Scroll to "API Key" section
3. Click "Reveal" and copy your API key

### 3. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

#### Required Heroku Secrets:
- `HEROKU_API_KEY`: Your Heroku API key
- `HEROKU_EMAIL`: Your Heroku account email
- `HEROKU_APP_NAME`: Your production Heroku app name
- `HEROKU_STAGING_APP_NAME`: Your staging Heroku app name (optional)

#### Django/Backend Secrets:
- `DJANGO_SECRET_KEY`: A secure secret key for Django
- `DATABASE_URL`: PostgreSQL connection string (Heroku provides this)

#### Supabase Secrets (from your .env):
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `SUPABASE_JWT_SECRET`: Your Supabase JWT secret

#### Stripe Secrets (if using payments):
- `STRIPE_SECRET_KEY`: Your Stripe secret key
- `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key
- `STRIPE_WEBHOOK_SECRET`: Your Stripe webhook secret

#### Other Services:
- `OPENAI_API_KEY`: Your OpenAI API key
- `BACKBLAZE_KEY_ID`: Backblaze key ID
- `BACKBLAZE_APPLICATION_KEY`: Backblaze application key
- `BACKBLAZE_BUCKET_ID`: Backblaze bucket ID
- `BACKBLAZE_BUCKET_NAME`: Backblaze bucket name
- `REDIS_URL`: Redis connection URL (if using Redis)
- `CLOUDFLARE_ACCOUNT_ID`: Cloudflare account ID
- `CLOUDFLARE_API_TOKEN`: Cloudflare API token

### 4. Add Heroku Addons

```bash
# Add PostgreSQL database
heroku addons:create heroku-postgresql:mini -a your-app-name

# Add Redis (for Celery/Channels)
heroku addons:create heroku-redis:mini -a your-app-name

# Get database URL
heroku config:get DATABASE_URL -a your-app-name
```

### 5. Configure Heroku Settings

```bash
# Set Python buildpack
heroku buildpacks:set heroku/python -a your-app-name

# Set environment variables
heroku config:set DJANGO_SETTINGS_MODULE=app.settings.production -a your-app-name
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com -a your-app-name
```

## Deployment Process

### Automatic Deployment (Recommended)

1. Push code to your GitHub repository
2. GitHub Actions will automatically:
   - Run tests
   - Deploy to staging (if pushing to `nh-dev` or `develop` branch)
   - Deploy to production (if pushing to `main` or `master` branch)

### Manual Deployment

```bash
# From the backend directory
cd apps/backend

# Add Heroku remote
heroku git:remote -a your-app-name

# Deploy using git subtree from root directory
git subtree push --prefix apps/backend heroku main

# Run migrations
heroku run python manage.py migrate -a your-app-name

# Create superuser
heroku run python manage.py createsuperuser -a your-app-name

# Collect static files
heroku run python manage.py collectstatic --noinput -a your-app-name
```

## Monitoring & Debugging

### View Logs
```bash
heroku logs --tail -a your-app-name
```

### Check App Status
```bash
heroku ps -a your-app-name
```

### Run Django Shell
```bash
heroku run python manage.py shell -a your-app-name
```

### Database Operations
```bash
# Create backup
heroku pg:backups:capture -a your-app-name

# Download backup
heroku pg:backups:download -a your-app-name
```

## Troubleshooting

### Common Issues

1. **Module Import Errors**: Ensure all dependencies are in `requirements.txt`

2. **Database Connection Issues**: Check `DATABASE_URL` is set correctly

3. **Static Files Not Loading**: 
   - Ensure `whitenoise` is installed
   - Run `collectstatic` command
   - Check `STATIC_ROOT` settings

4. **WebSocket Connection Issues**:
   - Ensure Redis addon is configured
   - Check `CHANNEL_LAYERS` settings

5. **Memory Issues**:
   - Monitor dyno metrics
   - Consider upgrading dyno type
   - Optimize worker processes

### Health Check Endpoint

The deployment workflow checks `/api/health/` endpoint. Ensure this is implemented:

```python
# In your urls.py
path('api/health/', health_check_view),

# In your views.py
def health_check_view(request):
    return JsonResponse({'status': 'healthy'})
```

## Scaling

```bash
# Scale web dynos
heroku ps:scale web=1:standard-1x -a your-app-name

# Scale worker dynos
heroku ps:scale worker=1:standard-1x -a your-app-name

# Scale for channels/websockets
heroku ps:scale channels=1:standard-1x -a your-app-name
```

## Security Notes

1. Never commit `.env` files
2. Use strong `SECRET_KEY` values
3. Enable Heroku's automatic SSL certificates
4. Regularly update dependencies
5. Use GitHub's Dependabot for security updates

## Cost Optimization

1. Use free tier for development/staging
2. Enable auto-sleep for staging apps
3. Use Heroku Scheduler instead of beat worker for periodic tasks
4. Monitor dyno usage and optimize accordingly

## Additional Resources

- [Heroku Django Documentation](https://devcenter.heroku.com/articles/django-app-configuration)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)